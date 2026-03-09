"""
WeatheringNet CLI

Usage:
    weatheringnet ali      --config configs/ali_config.yaml
    weatheringnet sdrs     --data-dir data/external
    weatheringnet dag      --output docs/dag.dot
    weatheringnet train    --data data/processed/cohort.parquet
    weatheringnet serve    --host 0.0.0.0 --port 8000
    weatheringnet info
"""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

app = typer.Typer(
    name="weatheringnet",
    help="Computational framework for transgenerational AID risk analysis",
    add_completion=False,
)
console = Console()


@app.command()
def info():
    """Display WeatheringNet version and module status."""
    from weatheringnet import __version__, __author__

    console.print(f"\n[bold cyan]WeatheringNet v{__version__}[/bold cyan]")
    console.print(f"Author: {__author__}")
    console.print()

    table = Table(title="Modules")
    table.add_column("Module", style="cyan")
    table.add_column("Description")
    table.add_column("Status", style="green")

    table.add_row("ali",       "Allostatic Load Index (NHANES)",          "✓ Ready")
    table.add_row("sdrs",      "Sociodemographic Risk Score (geospatial)", "✓ Ready")
    table.add_row("causal",    "DAG + Mediation Analysis",                 "✓ Ready")
    table.add_row("model",     "AID Risk Prediction (XGBoost + SHAP)",     "✓ Ready")
    table.add_row("dashboard", "Full-stack equity dashboard",               "✓ Ready")

    console.print(table)
    console.print()
    console.print("[dim]Grounded in: Foster (2023) — Maternal Stress and In-Utero AID Programming[/dim]")
    console.print("[dim]Bloomberg School of Public Health, Johns Hopkins University[/dim]\n")


@app.command()
def ali(
    config: Path = typer.Option("configs/ali_config.yaml", help="ALI config YAML"),
):
    """Run the Allostatic Load Index pipeline on NHANES data."""
    from weatheringnet.ali.pipeline import run_ali_pipeline
    console.print(f"[cyan]Running ALI pipeline with config: {config}[/cyan]")
    results = run_ali_pipeline(config)
    n = len(results["individual"])
    console.print(f"[green]✓ ALI computed for {n:,} participants[/green]")
    console.print(results["summary"].to_string(index=False))


@app.command()
def sdrs(
    data_dir: Path = typer.Option("data/external", help="Root dir for SDOH data files"),
    output: Path = typer.Option("data/processed/sdrs_tracts.parquet", help="Output path"),
):
    """Build the Sociodemographic Risk Score for all US census tracts."""
    from weatheringnet.sdrs.scorer import SDRSScorer
    console.print(f"[cyan]Building SDRS from {data_dir}[/cyan]")
    scorer = SDRSScorer(data_dir=data_dir)
    result = scorer.build()
    result.to_parquet(output, index=False)
    console.print(f"[green]✓ SDRS built for {len(result):,} census tracts → {output}[/green]")


@app.command()
def dag(
    output: Path = typer.Option("docs/weathering_dag.dot", help="Output path for DOT file"),
    format: str = typer.Option("dot", help="Output format: dot | dagitty"),
):
    """Export the WeatheringNet causal DAG."""
    from weatheringnet.causal.dag import WeatheringDAG
    d = WeatheringDAG()
    console.print(d.summary())
    output.parent.mkdir(parents=True, exist_ok=True)
    if format == "dagitty":
        output.write_text(d.to_dagitty())
    else:
        import networkx as nx
        nx.drawing.nx_pydot.write_dot(d.graph, str(output))
    console.print(f"[green]✓ DAG exported → {output}[/green]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host"),
    port: int = typer.Option(8000, help="Port"),
    reload: bool = typer.Option(False, help="Enable auto-reload (dev mode)"),
):
    """Launch the WeatheringNet dashboard API server."""
    import uvicorn
    console.print(f"[cyan]Starting WeatheringNet API at http://{host}:{port}[/cyan]")
    uvicorn.run(
        "weatheringnet.dashboard.backend.main:app",
        host=host, port=port, reload=reload,
    )


if __name__ == "__main__":
    app()
