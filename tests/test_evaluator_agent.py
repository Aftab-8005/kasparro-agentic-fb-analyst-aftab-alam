from src.agents.evaluator_agent import EvaluatorAgent
from src.schemas import InsightHypothesis


def test_validate_creative_underperformance():
    cfg = {
        "validation": {
            "ctr_drop_pct_threshold": 0.05
        }
    }

    evaluator = EvaluatorAgent(cfg)

    # Baseline CTR = 0.10
    baseline = [{"ctr": 0.10}]
    # Recent CTR = 0.05 → 50% drop → supported
    recent = [{"ctr": 0.05}]

    # Correct hypothesis object
    h = InsightHypothesis(
        id="H2",
        title="Creative underperformance",
        description="CTR has decreased",
        driver_type="creative_underperformance",
        expected_pattern="CTR declines",
        confidence_model=0.8
    )

    result = evaluator._validate_creative_underperformance(h, baseline, recent)

    assert result.verdict == "supported"
    assert result.final_confidence > 0.7
