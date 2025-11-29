from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PlannedSubtask:
    id: str
    agent: str
    description: str
    inputs: Dict[str, Any]


@dataclass
class Plan:
    overall_goal: str
    time_window_days: int
    subtasks: List[PlannedSubtask]


class PlannerAgent:
    """
    Planner Agent:
    - Takes marketer query + ROAS summary
    - Outputs a structured plan with subtasks for other agents
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def plan(self, query: str, roas_summary: Dict[str, Any]) -> Plan:
        # Basic heuristic: if query mentions "last 30 days", etc.
        # For now, use config default.
        window = self.cfg["analysis"]["roas_drop_window_days"]

        overall_goal = f"Diagnose ROAS changes and recommend creatives for query: {query}"

        subtasks = [
            PlannedSubtask(
                id="load_data",
                agent="DataAgent",
                description=f"Load and summarize performance for last {window} days and baseline.",
                inputs={"window_days": window},
            ),
            PlannedSubtask(
                id="generate_hypotheses",
                agent="InsightAgent",
                description="Generate hypotheses explaining ROAS change.",
                inputs={"window_days": window},
            ),
            PlannedSubtask(
                id="validate_hypotheses",
                agent="EvaluatorAgent",
                description="Quantitatively validate hypotheses and assign confidences.",
                inputs={"window_days": window},
            ),
            PlannedSubtask(
                id="generate_creatives",
                agent="CreativeGenerator",
                description="Propose new creative ideas for low-CTR campaigns.",
                inputs={"window_days": window},
            ),
        ]

        return Plan(
            overall_goal=overall_goal,
            time_window_days=window,
            subtasks=subtasks,
        )
