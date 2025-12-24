import streamlit as st
import pandas as pd
import sys
from pathlib import Path

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

st.sidebar.header("Filters")

indicator_label = st.sidebar.selectbox(
    "Indicator",
    list(core_indicators.values())
)

indicator_code = [
    k for k, v in core_indicators.items()
    if v == indicator_label
][0]

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