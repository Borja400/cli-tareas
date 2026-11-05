"""Interfaz de línea de órdenes: aquí solo hay órdenes, opciones y salida."""

from datetime import datetime
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__
from tareas.acciones import Resultado
from tareas.config import cargar
from tareas.errores import TareasError
from tareas.motor import Motor

app = typer.Typer(
    help="tareas: automatiza tareas repetitivas con tus ficheros.",
    no_args_is_help=True,
    add_completion=False,
)
consola = Console()
consola_err = Console(stderr=True)


def tamano_legible(n: int) -> str:
    """Convierte bytes en texto: 532 B, 1.2 KB, 3.4 MB..."""
    if n < 1024:
        return f"{n} B"

    tamano = float(n)
    unidad = "B"
    for unidad in ("KB", "MB", "GB", "TB"):
        tamano /= 1024
        if tamano < 1024:
            break
    return f"{tamano:.1f} {unidad}"


def _salir_con_error(error: TareasError) -> NoReturn:
    """Muestra un error humano en stderr y termina con su código."""
    consola_err.print(f"[red]Error:[/red] {escape(str(error))}")
    raise typer.Exit(code=error.codigo_salida)


def _cargar_config(ctx: typer.Context) -> list[dict]:
    """Carga la configuración o termina con el código de error adecuado."""
    try:
        return cargar(Path(ctx.obj))
    except TareasError as error:
        _salir_con_error(error)


def _contar(cantidad: int, singular: str, plural: str) -> str:
    """Devuelve «1 fichero» o «2 ficheros»."""
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def _pintar_resultados(
    nombre: str,
    resultados: list[Resultado],
    simular: bool,
) -> None:
    """Pinta la tabla de lo que se ha hecho o se simularía."""
    if not resultados:
        consola.print("Ningún fichero cumple el filtro.")
        return

    titulo = f"{nombre} (SIMULACIÓN: no se ha tocado nada)" if simular else nombre
    tabla = Table(title=escape(titulo))
    tabla.add_column("Fichero")
    tabla.add_column("Destino")
    tabla.add_column("Estado")

    for resultado in resultados:
        destino = str(resultado.destino) if resultado.destino is not None else "—"
        tabla.add_row(
            escape(resultado.origen.name),
            escape(destino),
            resultado.estado,
        )

    consola.print(tabla)

    total = len(resultados)
    hechos = sum(1 for resultado in resultados if resultado.estado == "hecho")
    simulados = sum(1 for resultado in resultados if resultado.estado == "simulado")
    saltados = sum(1 for resultado in resultados if resultado.estado == "saltado")
    consola.print(
        f"{_contar(total, 'fichero', 'ficheros')} · "
        f"{_contar(hechos, 'hecho', 'hechos')} · "
        f"{_contar(simulados, 'simulado', 'simulados')} · "
        f"{_contar(saltados, 'saltado', 'saltados')}"
    )

    if simular:
        consola.print("Para hacerlo de verdad, repite la orden sin --simular.")


@app.callback()
def principal(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option("--config", help="Ruta de acciones.json"),
    ] = Path("acciones.json"),
) -> None:
    """Guarda la configuración global de la CLI."""
    ctx.obj = config


@app.command()
def version() -> None:
    """Muestra la versión instalada."""
    consola.print(f"tareas {__version__}")


@app.command()
def listar(
    carpeta: Annotated[
        Path,
        typer.Argument(help="Carpeta que quieres ver (por defecto, la actual)."),
    ] = Path("."),
) -> None:
    """Lista los ficheros y carpetas de una carpeta en una tabla."""
    carpeta = carpeta.expanduser()

    if not carpeta.is_dir():
        consola_err.print(
            f"[red]Error:[/red] «{escape(str(carpeta))}» "
            "no existe o no es una carpeta."
        )
        raise typer.Exit(code=1)

    try:
        elementos = sorted(
            carpeta.iterdir(),
            key=lambda ruta: (not ruta.is_dir(), ruta.name.lower()),
        )
    except OSError as error:
        consola_err.print(
            f"[red]Error:[/red] no puedo leer «{escape(str(carpeta))}»: "
            f"{escape(str(error))}"
        )
        raise typer.Exit(code=1) from error

    if not elementos:
        consola.print(f"La carpeta «{escape(str(carpeta))}» está vacía.")
        return

    tabla = Table(title=f"Contenido de {escape(str(carpeta.resolve()))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño", justify="right")
    tabla.add_column("Modificado")

    for ruta in elementos:
        try:
            datos = ruta.stat()
        except OSError:
            # Enlace roto, fichero sin permisos o desaparecido: lo saltamos.
            continue

        es_carpeta = ruta.is_dir()
        tipo = "carpeta" if es_carpeta else (ruta.suffix.lower() or "(sin extensión)")
        tamano = "—" if es_carpeta else tamano_legible(datos.st_size)
        fecha = datetime.fromtimestamp(datos.st_mtime).strftime("%Y-%m-%d %H:%M")
        tabla.add_row(escape(ruta.name), tipo, tamano, fecha)

    consola.print(tabla)


@app.command()
def acciones(ctx: typer.Context) -> None:
    """Lista las acciones definidas en acciones.json."""
    lista = _cargar_config(ctx)

    tabla = Table(title="Acciones")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Descripción")

    for accion in lista:
        tabla.add_row(
            escape(accion["nombre"]),
            escape(accion["tipo"]),
            escape(accion["descripcion"]),
        )

    consola.print(tabla)


@app.command()
def validar(ctx: typer.Context) -> None:
    """Comprueba acciones.json y dice exactamente qué campo falla."""
    lista = _cargar_config(ctx)
    consola.print(f"[green]OK:[/green] {len(lista)} acciones válidas")


@app.command()
def ejecutar(
    ctx: typer.Context,
    nombre: Annotated[
        str,
        typer.Argument(help="Nombre de la acción (ver: tareas acciones)"),
    ],
    carpeta: Annotated[
        Path | None,
        typer.Argument(help="Carpeta sobre la que actuar"),
    ] = None,
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué haría sin tocar nada"),
    ] = False,
    si: Annotated[
        bool,
        typer.Option("--si", help="No pedir confirmación"),
    ] = False,
) -> None:
    """Ejecuta una acción sobre una carpeta."""
    try:
        lista = cargar(Path(ctx.obj))
        motor = Motor(lista)
        accion = motor.acciones.get(nombre)

        if accion is None:
            raise TareasError(
                f"No hay ninguna acción «{nombre}». "
                "Mira la lista con: tareas acciones"
            )

        if accion.destructiva and not simular and not si:
            if not typer.confirm(
                f"«{nombre}» borra ficheros. ¿Seguro?",
                default=False,
            ):
                consola.print("Operación cancelada.")
                raise typer.Exit(code=1)

        resultados = motor.ejecutar(nombre, carpeta, simular)
    except TareasError as error:
        _salir_con_error(error)

    _pintar_resultados(nombre, resultados, simular)


if __name__ == "__main__":
    app()
