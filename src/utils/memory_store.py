import json
from pathlib import Path
from typing import List, Dict, Any


class InsightMemory:
    """
    Simple short-term memory to store summaries of previous runs.
    Used for optional "iterative learning" across executions.
    """

    def __init__(self, path: Path, max_runs: int = 20):
        self.path = path
        self.max_runs = max_runs
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data: List[Dict[str, Any]] = json.load(f)
            except json.JSONDecodeError:
                self.data = []
        else:
            self.data = []

    def append_run(self, summary: Dict[str, Any]) -> None:
        self.data.append(summary)
        self.data = self.data[-self.max_runs :]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get_history(self) -> List[Dict[str, Any]]:
        return self.data
