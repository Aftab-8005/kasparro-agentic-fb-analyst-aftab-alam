import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class JSONLogger:
    """
    Simple JSON-lines logger:
    each log call appends a JSON object to logs/run_log.jsonl
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, payload: Dict[str, Any]):
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "payload": payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
