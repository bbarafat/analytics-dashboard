import pandas as pd

def latest_values(df: pd.DataFrame):
    return (
        df.sort_values("year")
        .groupby("country", as_index=False)
        .tail(1)
    )

def growth_rates(df: pd.DataFrame):
    first = df.groupby("country")["value"].first()
    last = df.groupby("country")["value"].last()
    return ((last - first) / first * 100).reset_index(name="growth_pct")