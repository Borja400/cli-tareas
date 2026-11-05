"""Punto de entrada de la CLI de tareas."""

import typer

from tareas import __version__

app = typer.Typer(help="Gestor de tareas por ficheros.")


@app.callback()
def main() -> None:
    """Gestor de tareas por ficheros."""


@app.command()
def version() -> None:
    """Muestra la versión del proyecto."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
