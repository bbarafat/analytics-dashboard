import pandas as pd

def filter_data(
    df: pd.DataFrame,
    indicators,
    countries,
    year_range,
):
    return df[
        (df["indicator"].isin(indicators))
        & (df["country"].isin(countries))
        & (df["year"].between(year_range[0], year_range[1]))
    ]