import os
import pandas as pd
import wbgapi as wb

west_africa = [
    'BEN', 'BFA', 'CPV', 'CIV', 'GMB', 'GHA', 'GIN', 'GNB',
    'LBR', 'MLI', 'MRT', 'NER', 'NGA', 'SEN', 'SLE', 'TGO'
]

def read_west_africa_data(
    core_indicators: dict,
    start: int,
    end: int,
    data_dir: str,
    name: str
):
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, name)

    if not os.path.isfile(file_path):
        print("Fetching West Africa data from World Bank API...")

        df = wb.data.DataFrame(
            list(core_indicators.keys()),
            west_africa,
            time=range(start, end + 1),
            labels=True
        )

        df = df.reset_index()

        year_cols = [c for c in df.columns if c.startswith("YR")]

        df_long = df.melt(
            id_vars=["economy", "Country", "series"],
            value_vars=year_cols,
            var_name="year",
            value_name="value"
        )

        df_long["year"] = (
            df_long["year"]
            .str.replace("YR", "", regex=False)
            .astype(int)
        )

        df_long = df_long.rename(
            columns={
                "economy": "country_code",
                "Country": "country",
                "series": "indicator",
            }
        )

        df_long.to_csv(file_path, index=False)
        print("Saved data to disk ✅")

    else:
        print("Reading data from disk...")
        df_long = pd.read_csv(file_path)
        print("Loaded cached data ✅")

    return df_long