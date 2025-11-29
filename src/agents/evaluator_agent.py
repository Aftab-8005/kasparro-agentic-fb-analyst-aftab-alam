from typing import List, Dict, Any


import numpy as np

from src.schemas import (
    InsightHypothesis,
    InsightEvidence,
    ValidatedInsight,
)


class EvaluatorAgent:
    """
    Evaluator Agent:
    - Takes hypotheses + aggregates
    - Produces ValidatedInsight with quantitative evidence & confidence
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def validate(
        self,
        hypotheses: List[InsightHypothesis],
        aggregates: Dict[str, Any],
    ) -> List[ValidatedInsight]:
        baseline = aggregates["baseline"]
        recent = aggregates["recent"]
        results: List[ValidatedInsight] = []

        for h in hypotheses:
            if h.driver_type == "creative_underperformance":
                v = self._validate_creative_underperformance(h, baseline, recent)
            elif h.driver_type == "audience_shift":
                v = self._validate_audience_shift(h, baseline, recent)
            elif h.driver_type == "roas_overall_drop":
                v = self._validate_roas_drop(h, baseline, recent)
            else:
                v = self._default_validation(h)
            results.append(v)

        return results

    def _default_validation(self, h: InsightHypothesis) -> ValidatedInsight:
        ev = InsightEvidence(
            metric="n/a",
            direction="flat",
            magnitude_pct=0.0,
            details="No specific quantitative rule for this hypothesis.",
        )
        q_conf = 0.3
        final_conf = (q_conf + h.confidence_model) / 2
        return ValidatedInsight(
            hypothesis=h,
            evidence=[ev],
            quantitative_confidence=q_conf,
            final_confidence=final_conf,
            verdict="partially_supported",
        )

    def _validate_roas_drop(
        self,
        h: InsightHypothesis,
        baseline: List[Dict[str, Any]],
        recent: List[Dict[str, Any]],
    ) -> ValidatedInsight:
        base_roas = (
            float(np.mean([r["roas"] for r in baseline])) if baseline else 0.0
        )
        rec_roas = float(np.mean([r["roas"] for r in recent])) if recent else 0.0

        change = 0.0
        if base_roas > 0:
            change = (rec_roas - base_roas) / base_roas

        direction = "down" if change < 0 else "up"
        evidence = InsightEvidence(
            metric="roas",
            direction=direction,
            magnitude_pct=abs(change),
            details=f"Baseline ROAS={base_roas:.2f}, recent ROAS={rec_roas:.2f}",
        )

        threshold = self.cfg["validation"]["roas_drop_pct_threshold"]
        q_conf = min(1.0, abs(change) / (threshold or 1e-6))
        final_conf = (q_conf + h.confidence_model) / 2
        verdict = "supported" if change < -threshold else "not_supported"

        return ValidatedInsight(
            hypothesis=h,
            evidence=[evidence],
            quantitative_confidence=q_conf,
            final_confidence=final_conf,
            verdict=verdict,
        )

    def _validate_creative_underperformance(
        self,
        h: InsightHypothesis,
        baseline: List[Dict[str, Any]],
        recent: List[Dict[str, Any]],
    ) -> ValidatedInsight:
        base_ctr = (
            float(np.mean([r["ctr"] for r in baseline])) if baseline else 0.0
        )
        rec_ctr = float(np.mean([r["ctr"] for r in recent])) if recent else 0.0

        change = 0.0
        if base_ctr > 0:
            change = (rec_ctr - base_ctr) / base_ctr

        direction = "down" if change < 0 else "up"
        evidence = InsightEvidence(
            metric="ctr",
            direction=direction,
            magnitude_pct=abs(change),
            details=f"Baseline CTR={base_ctr:.4f}, recent CTR={rec_ctr:.4f}",
        )

        threshold = self.cfg["validation"]["ctr_drop_pct_threshold"]
        q_conf = min(1.0, abs(change) / (threshold or 1e-6))
        final_conf = (q_conf + h.confidence_model) / 2
        verdict = "supported" if change < -threshold else "not_supported"

        return ValidatedInsight(
            hypothesis=h,
            evidence=[evidence],
            quantitative_confidence=q_conf,
            final_confidence=final_conf,
            verdict=verdict,
        )

    def _validate_audience_shift(
        self,
        h: InsightHypothesis,
        baseline: List[Dict[str, Any]],
        recent: List[Dict[str, Any]],
    ) -> ValidatedInsight:
        spend_by_aud_base: Dict[str, float] = {}
        spend_by_aud_rec: Dict[str, float] = {}

        for r in baseline:
            a = r["audience_type"]
            spend_by_aud_base[a] = spend_by_aud_base.get(a, 0.0) + float(r["spend"])

        for r in recent:
            a = r["audience_type"]
            spend_by_aud_rec[a] = spend_by_aud_rec.get(a, 0.0) + float(r["spend"])

        total_base = sum(spend_by_aud_base.values()) or 1e-6
        total_rec = sum(spend_by_aud_rec.values()) or 1e-6

        max_shift = 0.0
        details_list = []
        for aud, b_spend in spend_by_aud_base.items():
            r_spend = spend_by_aud_rec.get(aud, 0.0)
            b_share = b_spend / total_base
            r_share = r_spend / total_rec
            shift = r_share - b_share
            max_shift = max(max_shift, abs(shift))
            details_list.append(f"{aud}: baseline={b_share:.2%}, recent={r_share:.2%}")

        evidence = InsightEvidence(
            metric="spend_share_by_audience",
            direction="shift",
            magnitude_pct=max_shift,
            details="; ".join(details_list),
        )

        q_conf = min(1.0, max_shift / 0.15)  # 15pp threshold
        final_conf = (q_conf + h.confidence_model) / 2
        verdict = "supported" if max_shift > 0.15 else "not_supported"

        return ValidatedInsight(
            hypothesis=h,
            evidence=[evidence],
            quantitative_confidence=q_conf,
            final_confidence=final_conf,
            verdict=verdict,
        )
