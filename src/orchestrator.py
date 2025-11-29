from pathlib import Path
from typing import Dict, Any

import pandas as pd

from src.utils.config_loader import load_config
from src.utils.logging_utils import JSONLogger
from src.utils.data_loader import load_dataframe, df_to_rows
from src.utils.memory_store import InsightMemory

from src.agents.planner import PlannerAgent
from src.agents.data_agent import DataAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator_agent import EvaluatorAgent
from src.agents.creative_generator import CreativeGenerator

from src.schemas import (
    InsightsReport,
    CreativesReport,
)




class Orchestrator:
    """
    Runs the full multi-agent pipeline:
    1. Planner
    2. DataAgent
    3. InsightAgent
    4. EvaluatorAgent
    5. CreativeGenerator
    """

    def __init__(self):
        self.cfg = load_config()

        log_path = Path(self.cfg["logging"]["json_log_path"])
        self.logger = JSONLogger(log_path)

        mem_path = Path(self.cfg["memory"]["path"])
        self.memory = InsightMemory(mem_path, self.cfg["memory"]["max_runs"])

        self.data_agent = DataAgent(self.cfg)
        self.insight_agent = InsightAgent(self.cfg)
        self.evaluator = EvaluatorAgent(self.cfg)
        self.creative_gen = CreativeGenerator(self.cfg)
        self.planner = PlannerAgent(self.cfg)

    def run(self, query: str) -> Dict[str, Any]:
        self.logger.log("start_run", {"query": query})

        df = load_dataframe(self.cfg)
        self.logger.log("data_loaded", {"rows": len(df)})

        # Step 1 — summarize ROAS
        window = self.cfg["analysis"]["roas_drop_window_days"]
        roas_summary = self.data_agent.summarize_roas(window)
        self.logger.log("roas_summary", roas_summary.dict())

        # Step 2 — generate plan
        plan = self.planner.plan(query, roas_summary.dict())
        self.logger.log("plan_created", {"subtasks": [s.id for s in plan.subtasks]})

        # Step 3 — aggregates
        aggs = self.data_agent.aggregate_for_insights(window)
        self.logger.log("aggregates_ready", {"baseline": len(aggs["baseline"]), "recent": len(aggs["recent"])})

        # Step 4 — insight generation
        hypotheses = self.insight_agent.generate_hypotheses(
            roas_summary.dict(), aggs
        )
        self.logger.log("hypotheses_generated", {"count": len(hypotheses)})

        # Step 5 — validation
        validated = self.evaluator.validate(hypotheses, aggs)
        self.logger.log("insights_validated", {"count": len(validated)})

        # Step 6 — creative ideas
        ideas = self.creative_gen.generate(df)
        self.logger.log("creative_ideas", {"count": len(ideas)})

        # Step 7 — write final reports
        insights_report = InsightsReport(
            query=query,
            roas_summary=roas_summary,
            top_insights=validated,
        )

        creatives_report = CreativesReport(query=query, ideas=ideas)

        self._write_reports(insights_report, creatives_report)
        self.logger.log("reports_written", {})

        # Step 8 — memory
        if self.cfg["memory"]["enabled"]:
            self.memory.append_run(
                {
                    "query": query,
                    "top_insights": [i.hypothesis.id for i in validated],
                    "roas_recent": roas_summary.recent_roas,
                }
            )
            self.logger.log("memory_updated", {"entries": len(self.memory.get_history())})

        self.logger.log("end_run", {})

        return {
            "insights": insights_report,
            "creatives": creatives_report,
        }

    def _write_reports(self, insights: InsightsReport, creatives: CreativesReport):
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True, parents=True)

        # insights.json
        ins_path = reports_dir / "insights.json"
        with open(ins_path, "w", encoding="utf-8") as f:
            f.write(insights.json(indent=2))

        # creatives.json
        cr_path = reports_dir / "creatives.json"
        with open(cr_path, "w", encoding="utf-8") as f:
            f.write(creatives.json(indent=2))

        # report.md (human readable)
        md_path = reports_dir / "report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._markdown_report(insights, creatives))

    def _markdown_report(self, insights: InsightsReport, creatives: CreativesReport) -> str:
        lines = []
        lines.append(f"# Kasparro — Agentic Facebook Analyst Report\n")
        lines.append(f"### Query: {insights.query}\n")
        lines.append("## ROAS Summary")
        lines.append(f"- Baseline ROAS: **{insights.roas_summary.baseline_roas:.2f}**")
        lines.append(f"- Recent ROAS: **{insights.roas_summary.recent_roas:.2f}**")
        lines.append(f"- % Change: **{insights.roas_summary.pct_change * 100:.2f}%**")
        lines.append("")
        lines.append("## Top Insights")
        for i in insights.top_insights:
            lines.append(f"### {i.hypothesis.id} — {i.hypothesis.title}")
            lines.append(f"- Verdict: **{i.verdict}**")
            lines.append(f"- Final Confidence: **{i.final_confidence:.2f}**")
            for ev in i.evidence:
                lines.append(f"  - {ev.metric}: {ev.direction}, {ev.magnitude_pct*100:.2f}% — {ev.details}")
            lines.append("")
        lines.append("## Creative Recommendations")
        for c in creatives.ideas:
            lines.append(f"### {c.campaign_name} — {c.audience_type}")
            lines.append(f"- Current CTR: {c.current_ctr:.4f}")
            lines.append(f"- Problem: {c.problem_statement}")
            lines.append("**New Headlines:**")
            for h in c.new_headlines:
                lines.append(f"- {h}")
            lines.append("**New Primary Texts:**")
            for t in c.new_primary_texts:
                lines.append(f"- {t}")
            lines.append("**CTAs:**")
            for z in c.new_ctas:
                lines.append(f"- {z}")
            lines.append("")
        return "\n".join(lines)
