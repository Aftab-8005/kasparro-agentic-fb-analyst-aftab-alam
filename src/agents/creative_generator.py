from typing import List

import pandas as pd

from ..schemas import CreativeIdea


class CreativeGenerator:
    """
    Creative Improvement Generator:
    - Finds low-CTR campaigns
    - Proposes new creative ideas (headlines, text, CTAs) grounded in existing messaging
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def generate(self, df: pd.DataFrame) -> List[CreativeIdea]:
        q = self.cfg["creative"]["low_ctr_quantile"]
        min_impr = self.cfg["analysis"]["min_impressions"]

        df = df[df["impressions"] >= min_impr].copy()
        if df.empty:
            return []

        threshold = df["ctr"].quantile(q)
        low = df[df["ctr"] <= threshold]

        ideas: List[CreativeIdea] = []
        max_per_aud = self.cfg["creative"]["max_creatives_per_audience"]

        grouped = low.groupby("audience_type")
        for aud, block in grouped:
            block = block.sort_values("ctr").head(max_per_aud)
            for _, r in block.iterrows():
                ideas.append(
                    self._ideas_for_row(
                        campaign_name=str(r["campaign_name"]),
                        adset_name=str(r["adset_name"]),
                        audience_type=str(r["audience_type"]),
                        platform=str(r["platform"]),
                        country=str(r["country"]),
                        ctr=float(r["ctr"]),
                        creative_message=str(r["creative_message"]),
                    )
                )

        return ideas

    def _ideas_for_row(
        self,
        campaign_name: str,
        adset_name: str,
        audience_type: str,
        platform: str,
        country: str,
        ctr: float,
        creative_message: str,
    ) -> CreativeIdea:
        # very simple pseudo keyword extraction based on existing message
        tokens = [t.strip(".,!?") for t in creative_message.split() if len(t) > 3]
        unique = list(dict.fromkeys(tokens))
        core_keywords = unique[:3] if len(unique) >= 3 else unique

        base_benefit = "comfort"
        for t in tokens:
            low = t.lower()
            if "fit" in low:
                base_benefit = "fit"
            if "cool" in low or "breath" in low:
                base_benefit = "breathability"

        audience_label = audience_type.replace("_", " ").title()

        headlines = [
            f"{audience_label} deserve all-day {base_benefit}, not compromises.",
            f"Stop settling for scratchy underwear — upgrade your {base_benefit} today.",
            f"{base_benefit.title()} that actually lasts through your busiest days.",
        ]

        primary_texts = [
            f"Your current ads mention: {' '.join(core_keywords)}. "
            "Turn that into a clear promise: show how it feels in real life (gym, office, travel).",
            "Test a problem→solution variant: call out chafing, ride-up or sweat in the opening line, "
            "then position your product as the fix.",
            "Simplify the copy: one core benefit per creative, with a clear hook in the first 2 seconds.",
        ]

        ctas = [
            "Shop Comfort Now",
            "Upgrade Your Top Drawer",
            "Try The Difference Today",
        ]

        return CreativeIdea(
            campaign_name=campaign_name,
            adset_name=adset_name,
            audience_type=audience_type,
            platform=platform,
            country=country,
            current_ctr=ctr,
            problem_statement=(
                "CTR is in the lowest quartile for this audience. Creative likely fails to deliver a sharp hook "
                "or a clear benefit early enough."
            ),
            new_headlines=headlines[: self.cfg["creative"]["num_ideas_per_creative"]],
            new_primary_texts=primary_texts[
                : self.cfg["creative"]["num_ideas_per_creative"]
            ],
            new_ctas=ctas[: self.cfg["creative"]["num_ideas_per_creative"]],
        )
