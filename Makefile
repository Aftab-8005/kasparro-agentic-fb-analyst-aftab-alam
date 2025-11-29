# Makefile for Kasparro Agentic FB Analyst - Aftab Alam

# Activate virtual environment (Windows)
VENV = .venv\Scripts\activate

# ------------------------
# Basic Commands
# ------------------------

install:
	$(VENV) && pip install -r requirements.txt

run:
	$(VENV) && python -m src.run "Analyze ROAS drop in last 7 days"

test:
	$(VENV) && pytest -q

lint:
	$(VENV) && flake8 src

report:
	$(VENV) && python -m src.run "Generate analysis report"

clean:
	del /Q logs\*.jsonl
	del /Q reports\*.json
	del /Q reports\report.md

# ------------------------
# Developer Utility
# ------------------------

freeze:
	$(VENV) && pip freeze > requirements.txt
