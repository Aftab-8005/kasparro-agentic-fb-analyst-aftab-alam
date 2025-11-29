from datetime import timedelta
from typing import Dict, Any

import pandas as pd

from ..schemas import ROASSummary
from ..utils.data_loader import load_dataframe


class DataAgent:
    """
    Data Agent:
    - Loads the main CSV into a DataFrame
    - Computes ROAS summaries and aggregates for other agents
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._df: pd.DataFrame | None = None

    def load(self) -> pd.DataFrame:
        if self._df is None:
            self._df = load_dataframe(self.cfg)
        return self._df

    def summarize_roas(self, window_days: int) -> ROASSummary:
        df = self.load().sort_values("date")

        last_date = df["date"].max()
        recent_start = last_date - timedelta(days=window_days - 1)
        baseline_end = recent_start - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=window_days - 1)

        recent_mask = (df["date"] >= recent_start) & (df["date"] <= last_date)
        baseline_mask = (df["date"] >= baseline_start) & (df["date"] <= baseline_end)

        recent_roas = df.loc[recent_mask, "roas"].mean()
        baseline_roas = df.loc[baseline_mask, "roas"].mean()

        pct_change = 0.0
        if baseline_roas and baseline_roas != 0:
            pct_change = (recent_roas - baseline_roas) / baseline_roas

        return ROASSummary(
            baseline_roas=float(baseline_roas),
            recent_roas=float(recent_roas),
            pct_change=float(pct_change),
            baseline_date_range=f"{baseline_start.date()} to {baseline_end.date()}",
            recent_date_range=f"{recent_start.date()} to {last_date.date()}",
        )

    def aggregate_for_insights(self, window_days: int) -> Dict[str, Any]:
        """
        Returns dict with 'baseline' and 'recent' aggregated by (campaign_name, audience_type)
        including spend, impressions, clicks, purchases, revenue, ctr, roas, cvr.
        """
        df = self.load().sort_values("date")

        last_date = df["date"].max()
        recent_start = last_date - timedelta(days=window_days - 1)
        baseline_end = recent_start - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=window_days - 1)

        recent = df[(df["date"] >= recent_start) & (df["date"] <= last_date)]
        baseline = df[(df["date"] >= baseline_start) & (df["date"] <= baseline_end)]

        def agg(block: pd.DataFrame) -> pd.DataFrame:
            if block.empty:
                return pd.DataFrame(
                    columns=[
                        "campaign_name",
                        "audience_type",
                        "spend",
                        "impressions",
                        "clicks",
                        "purchases",
                        "revenue",
                        "ctr",
                        "roas",
                        "cvr",
                    ]
                )
            g = (
                block.groupby(["campaign_name", "audience_type"], as_index=False)
                .agg(
                    spend=("spend", "sum"),
                    impressions=("impressions", "sum"),
                    clicks=("clicks", "sum"),
                    purchases=("purchases", "sum"),
                    revenue=("revenue", "sum"),
                )
                .assign(
                    ctr=lambda d: d["clicks"] / d["impressions"].clip(lower=1),
                    roas=lambda d: d["revenue"] / d["spend"].clip(lower=1e-6),
                    cvr=lambda d: d["purchases"] / d["clicks"].clip(lower=1),
                )
            )
            return g

        return {
            "baseline": agg(baseline).to_dict(orient="records"),
            "recent": agg(recent).to_dict(orient="records"),
        }

    def low_ctr_creatives(self, quantile: float, min_impressions: int) -> pd.DataFrame:
        """
        Returns DataFrame of rows in lowest CTR quantile with enough impressions.
        """
        df = self.load()
        df = df[df["impressions"] >= min_impressions].copy()
        if df.empty:
            return df
        q = df["ctr"].quantile(quantile)
        return df[df["ctr"] <= q]
