import click
from src.orchestrator import Orchestrator


@click.command()
@click.argument("query", nargs=-1)
def main(query):
    query_text = " ".join(query)
    orch = Orchestrator()
    orch.run(query_text)

    print("\n✨ Run Complete! Check the reports folder:")
    print(" - reports/report.md")
    print(" - reports/insights.json")
    print(" - reports/creatives.json")
    print("\n")


if __name__ == "__main__":
    main()
