import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
import plotly.express as px

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from pipeline.load import read_west_africa_data

core_indicators = {
    'NY.GDP.PCAP.CD': 'GDP per capita',
    'SP.POP.TOTL': 'Population',
    'SP.DYN.LE00.IN': 'Life expectancy',
    'SE.ADT.LITR.ZS': 'Literacy rate',
    'SH.DYN.MORT': 'Child mortality',
    'IT.NET.USER.ZS': 'Internet users %',
    'SL.UEM.TOTL.ZS': 'Unemployment',
    'EG.ELC.ACCS.ZS': 'Electricity access',
    'SI.POV.DDAY': 'Poverty rate',
    'NY.GDP.MKTP.KD.ZG': 'GDP growth'
}

st.set_page_config(
    page_title="West Africa World Bank Dashboard",
    layout="wide"
)

st.title("West Africa World Bank Indicators")
st.write("Interactive dashboard using live World Bank data.")

st.sidebar.header("Data Controls")

start_year = st.sidebar.number_input(
    "Start year",
    min_value=1957,
    max_value=2023,
    value=2010,
    step=1
)

end_year = st.sidebar.number_input(
    "End year",
    min_value=start_year,
    max_value=2025,
    value=2024,
    step=1
)

@st.cache_data(show_spinner=True)
def load_data(start_year, end_year):
    return read_west_africa_data(
        core_indicators=core_indicators,
        start=start_year,
        end=end_year,
        data_dir="data/processed",
        name="west_africa_world_bank.csv"
    )
df = load_data(start_year, end_year)
st.write("Rows loaded:", df.shape[0])
st.dataframe(df.head())

st.markdown("## 📊 Key Metrics")

st.sidebar.header("Filters")

indicator_label = st.sidebar.selectbox(
    "Indicator",
    list(core_indicators.values())
)

indicator_code = [
    k for k, v in core_indicators.items()
    if v == indicator_label
][0]

st.markdown("---")

country_options = sorted(df["country"].unique())

selected_countries = st.sidebar.multiselect(
    "Countries",
    country_options,
    default=country_options[:5]
)

filtered = df[
    (df["indicator"] == indicator_code)
    & (df["country"].isin(selected_countries))
].copy()

if filtered.empty:
    st.warning("No data available for this selection.")
    st.stop()

filtered_sorted = filtered.sort_values(["country", "year"])

base_values = (
    filtered_sorted
    .groupby("country")
    .first()["value"]
)

filtered_sorted["growth_index"] = (
    filtered_sorted["value"]
    / filtered_sorted["country"].map(base_values)
    * 100
)
latest_year = filtered["year"].max()
latest_df = filtered[filtered["year"] == latest_year]

latest_avg = latest_df["value"].mean()

start_df = filtered.groupby("country").first()["value"]
end_df = filtered.groupby("country").last()["value"]

growth_pct = ((end_df - start_df) / start_df * 100).replace(
    [np.inf, -np.inf], np.nan
)

avg_growth = growth_pct.mean()

top_country = (
    latest_df.groupby("country")["value"]
    .mean()
    .idxmax()
)    

c1, c2, c3, c4 = st.columns(4)

c1.metric("Latest year", int(latest_year))
c2.metric("Avg value (latest)", f"{latest_avg:,.2f}")
c3.metric("Avg growth (%)", f"{avg_growth:,.2f}%")
c4.metric("Top country", top_country)

st.markdown("## 📈 Trends & Comparisons")

tab_trends, tab_growth = st.tabs(
    ["📈 Indicator Trends", "🚀 Growth Over Time"]
)

with tab_trends:
    st.subheader("Time Series")

    fig_ts = px.line(
        filtered,
        x="year",
        y="value",
        color="country",
        markers=True
    )

    st.plotly_chart(fig_ts, use_container_width=True)

    st.markdown("---")

    st.subheader(f"Country Ranking ({latest_year})")

    rank = (
        latest_df.groupby("country")["value"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig_rank = px.bar(rank, x="country", y="value")
    st.plotly_chart(fig_rank, use_container_width=True)

with tab_growth:
    st.subheader("Indexed Growth Over Time")
    st.caption(
        "All countries start at their first available year (index = 100). "
        "This shows relative growth trajectories over time."
    )

    chart_type = st.radio(
        "Chart Type",
        ["Line Chart", "Racing Bar Chart"],
        horizontal=True
    )
    
    animate = st.checkbox(
        "▶️ Animate growth over time",
        value=True
    )
    
    if chart_type == "Racing Bar Chart":
        # Get the latest value for each country at each year for racing bars
        racing_data = filtered_sorted.groupby(["year", "country"])["growth_index"].last().reset_index()
        
        if animate:
            fig_growth = px.bar(
                racing_data,
                x="growth_index",
                y="country",
                color="country",
                animation_frame="year",
                range_x=[0, racing_data["growth_index"].max() * 1.1],
                orientation='h',
                title=f"{indicator_label} - Growth Index"
            )
            
            fig_growth.update_layout(
                xaxis_title="Growth Index (Base = 100)",
                yaxis_title="",
                showlegend=False,
                height=500,
                transition={"duration": 500}
            )
            
            # Add play/pause buttons
            fig_growth.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
            fig_growth.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300
            
        else:
            # Static bar chart for latest year
            latest_racing = racing_data[racing_data["year"] == racing_data["year"].max()]
            fig_growth = px.bar(
                latest_racing.sort_values("growth_index"),
                x="growth_index",
                y="country",
                color="country",
                orientation='h',
                title=f"{indicator_label} - Growth Index ({latest_racing['year'].iloc[0]})"
            )
            fig_growth.update_layout(showlegend=False)
    
    else:  # Line Chart
        if animate:
            # Build cumulative data for animation
            frames = []
            years = sorted(filtered_sorted["year"].unique())

            for y in years:
                frame_df = filtered_sorted[filtered_sorted["year"] <= y].copy()
                frame_df["frame_year"] = y
                frames.append(frame_df)

            animated_df = pd.concat(frames, ignore_index=True)
            
            fig_growth = px.line(
                animated_df,
                x="year",
                y="growth_index",
                color="country",
                animation_frame="frame_year",
                markers=True,
                range_x=[filtered_sorted["year"].min(), filtered_sorted["year"].max()],
                range_y=[0, animated_df["growth_index"].max() * 1.1]
            )
            
            fig_growth.update_layout(
                yaxis_title="Growth Index (Base = 100)",
                xaxis_title="Year",
                legend_title="Country",
                transition={"duration": 500}
            )
            
            # Ensure consistent axes
            fig_growth.update_xaxes(range=[filtered_sorted["year"].min(), filtered_sorted["year"].max()])
            fig_growth.update_yaxes(range=[0, animated_df["growth_index"].max() * 1.1])
            
        else:
            fig_growth = px.line(
                filtered_sorted,
                x="year",
                y="growth_index",
                color="country",
                markers=True
            )

            fig_growth.update_layout(
                yaxis_title="Growth Index (Base = 100)",
                xaxis_title="Year",
                legend_title="Country"
            )

    st.plotly_chart(fig_growth, use_container_width=True)


if st.sidebar.button("🔄 Refresh World Bank data"):
    load_data.clear()
    st.experimental_rerun()