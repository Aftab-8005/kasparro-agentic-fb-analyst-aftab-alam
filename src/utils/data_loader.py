from pathlib import Path
from typing import List
import pandas as pd
from src.schemas import RowMetrics



def load_dataframe(cfg: dict) -> pd.DataFrame:
    csv_path = Path(cfg["data"]["csv_path"])
    df = pd.read_csv(csv_path)

    required = [
        "campaign_name", "adset_name", "date", "spend", "impressions",
        "clicks", "ctr", "purchases", "revenue", "roas",
        "creative_type", "creative_message", "audience_type",
        "platform", "country",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["date"] = pd.to_datetime(df["date"])

    if cfg["data"]["use_sample"]:
        df = df.sample(cfg["data"]["sample_n_rows"], random_state=cfg["random_seed"])

    return df


def df_to_rows(df: pd.DataFrame) -> List[RowMetrics]:
    rows = []
    for _, r in df.iterrows():
        rows.append(
            RowMetrics(
                campaign_name=str(r["campaign_name"]),
                adset_name=str(r["adset_name"]),
                date=str(r["date"].date()),
                spend=float(r["spend"]),
                impressions=float(r["impressions"]),
                clicks=float(r["clicks"]),
                ctr=float(r["ctr"]),
                purchases=float(r["purchases"]),
                revenue=float(r["revenue"]),
                roas=float(r["roas"]),
                creative_type=str(r["creative_type"]),
                creative_message=str(r["creative_message"]),
                audience_type=str(r["audience_type"]),
                platform=str(r["platform"]),
                country=str(r["country"]),
            )
        )
    return rows
