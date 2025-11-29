from typing import List, Dict, Any
import numpy as np

from ..schemas import InsightHypothesis


class InsightAgent:
    """
    Insight Agent:
    - Takes ROAS summary + aggregated data
    - Generates qualitative hypotheses (H1, H2, H3...)
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def generate_hypotheses(
        self,
        roas_summary: Dict[str, Any],
        aggregates: Dict[str, Any],
    ) -> List[InsightHypothesis]:
        pct_change = roas_summary["pct_change"]
        hyps: List[InsightHypothesis] = []

        baseline = aggregates["baseline"]
        recent = aggregates["recent"]

        def avg(metric: str, recs: List[Dict[str, Any]]) -> float:
            vals = [float(r[metric]) for r in recs if metric in r]
            return float(np.mean(vals)) if vals else 0.0

        baseline_ctr = avg("ctr", baseline)
        recent_ctr = avg("ctr", recent)
        baseline_roas = avg("roas", baseline)
        recent_roas = avg("roas", recent)

        ctr_drop = (
            (baseline_ctr - recent_ctr) / baseline_ctr if baseline_ctr > 0 else 0.0
        )
        roas_drop = (
            (baseline_roas - recent_roas) / baseline_roas if baseline_roas > 0 else 0.0
        )

        # H1: Overall ROAS drop
        if roas_drop > self.cfg["validation"]["roas_drop_pct_threshold"]:
            hyps.append(
                InsightHypothesis(
                    id="H1",
                    title="ROAS has materially decreased in the recent period",
                    description=(
                        "Overall ROAS is lower vs the previous window. "
                        "We should decompose whether this is driven by CTR, "
                        "conversion rate, or audience mix."
                    ),
                    driver_type="roas_overall_drop",
                    expected_pattern="Recent ROAS significantly lower than baseline.",
                    confidence_model=0.9,
                )
            )

        # H2: Creative fatigue / underperformance
        if ctr_drop > self.cfg["validation"]["ctr_drop_pct_threshold"]:
            hyps.append(
                InsightHypothesis(
                    id="H2",
                    title="Creative fatigue or underperformance (CTR is dropping)",
                    description=(
                        "Average CTR has declined, suggesting creatives are less engaging "
                        "or overexposed to the same audiences."
                    ),
                    driver_type="creative_underperformance",
                    expected_pattern="CTR declines across multiple campaigns/audiences.",
                    confidence_model=0.85,
                )
            )

        # H3: Audience mix shift
        baseline_aud = self._audience_spend_share(baseline)
        recent_aud = self._audience_spend_share(recent)
        if self._has_audience_shift(baseline_aud, recent_aud):
            hyps.append(
                InsightHypothesis(
                    id="H3",
                    title="Audience mix shift impacting performance",
                    description=(
                        "Spend has shifted between audience segments; some of the new segments "
                        "may have lower intent or weaker performance."
                    ),
                    driver_type="audience_shift",
                    expected_pattern="Significant change in spend share between audience_type.",
                    confidence_model=0.75,
                )
            )

        return hyps

    def _audience_spend_share(self, recs: List[Dict[str, Any]]) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for r in recs:
            aud = r.get("audience_type", "unknown")
            totals[aud] = totals.get(aud, 0.0) + float(r.get("spend", 0.0))
        total = sum(totals.values()) or 1e-6
        return {k: v / total for k, v in totals.items()}

    def _has_audience_shift(self, base: Dict[str, float], recent: Dict[str, float]) -> bool:
        """
        Detects if any audience segment’s spend share changed by more than 15 percentage points.
        """
        for aud, b_share in base.items():
            r_share = recent.get(aud, 0.0)
            if abs(r_share - b_share) > 0.15:  # 15pp
                return True
        return False
