import subprocess as sp
import typer
import rich

from rich.console import Console

from mw_dube_dashboard.preprocess import make
from mw_dube_dashboard.utils import src, pkg

console = Console()

app = typer.Typer(
    name="mwdash",
    help="A dashboard to visualize the minimum wage in different countries, and compare it to the Dube prescription",
    no_args_is_help=True,
    rich_help_panel="rich",
    rich_markup_mode="rich",
)


@app.command(
    name="run",
    help="Run the dashboard",
)
def run():
    dash = (src / "dash.py").resolve()
    sp.run(["streamlit", "run", dash])
    
    
@app.command(
    name="preprocess",
    help="Preprocess the data",
)
def preprocess():
    df = make()
    console.print("Preprocessing complete", style="bold green")
    console.print(df.head(20), style="bold green")