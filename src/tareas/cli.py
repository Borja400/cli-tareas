"""Punto de entrada de la CLI de tareas."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tareas import __version__

app = typer.Typer(help="Gestor de tareas por ficheros.")
consola = Console()


@app.callback()
def main() -> None:
    """Gestor de tareas por ficheros."""


@app.command()
def version() -> None:
    """Muestra la versión del proyecto."""
    typer.echo(__version__)


@app.command()
def listar() -> None:
    """Muestra las acciones definidas en acciones.json."""
    ruta = Path("acciones.json")

    if not ruta.exists():
        consola.print("No hay acciones definidas todavía")
        return

    acciones = json.loads(ruta.read_text(encoding="utf-8"))

    tabla = Table(title="Acciones")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Descripción")

    for accion in acciones:
        tabla.add_row(
            accion.get("nombre", ""),
            accion.get("tipo", ""),
            accion.get("descripcion", ""),
        )

    consola.print(tabla)


if __name__ == "__main__":
    app()
