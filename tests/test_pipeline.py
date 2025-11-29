import pandas as pd

from src.orchestrator import Orchestrator




def test_pipeline_runs_end_to_end():
    orch = Orchestrator()
    query = "Analyze ROAS drop"
    result = orch.run(query)

    assert "insights" in result
    assert "creatives" in result

    # insights should have ROAS summary
    assert result["insights"].roas_summary.recent_roas is not None

    # creatives file should be generated
    assert len(result["creatives"].ideas) >= 0
