"""Clases que aplican cada tipo de acción sobre los ficheros."""

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tareas.errores import AccionNoValida, TareasError


@dataclass
class Resultado:
    """Informe de lo que pasó con un fichero."""

    origen: Path
    destino: Path | None
    estado: str  # "hecho", "simulado" o "saltado"


def destino_libre(destino: Path, reservados: set[Path] | None = None) -> Path:
    """Devuelve un destino que no existe ni está reservado en una simulación."""
    libre = destino
    numero = 1
    while libre.exists() or (reservados is not None and libre in reservados):
        libre = destino.with_name(f"{destino.stem} ({numero}){destino.suffix}")
        numero += 1
    return libre


class Accion(ABC):
    """Base común de todas las acciones."""

    tipo = ""
    destructiva = False
    _registro: dict[str, type["Accion"]] = {}

    def __init__(self, config: dict) -> None:
        self.nombre = config["nombre"]
        self.descripcion = config["descripcion"]
        self.config = config

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.tipo:
            Accion._registro[cls.tipo] = cls

    @staticmethod
    def desde_config(config: dict) -> "Accion":
        """Fábrica: convierte el diccionario del JSON en la clase que toca."""
        clase = Accion._registro.get(config.get("tipo", ""))
        if clase is None:
            raise AccionNoValida(
                config.get("nombre", "?"),
                "tipo",
                "no hay ninguna clase para ese tipo",
            )
        return clase(config)

    def ejecutar(self, ficheros: list[Path], simular: bool) -> list[Resultado]:
        """Aplica la acción a todos los ficheros seleccionados."""
        return [
            self.aplicar(fichero, numero, simular)
            for numero, fichero in enumerate(ficheros, start=1)
        ]

    @abstractmethod
    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        """Aplica la acción a un solo fichero."""


class Mover(Accion):
    """Mueve el fichero a otra carpeta."""

    tipo = "mover"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta = Path(self.config["destino"]).expanduser()
        destino = destino_libre(carpeta / fichero.name)

        if not simular:
            try:
                carpeta.mkdir(parents=True, exist_ok=True)
                shutil.move(fichero, destino)
            except OSError as error:
                raise TareasError(
                    f"No se pudo mover «{fichero.name}»: {error}"
                ) from error

        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Copiar(Accion):
    """Copia el fichero a otra carpeta sin borrar el original."""

    tipo = "copiar"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta = Path(self.config["destino"]).expanduser()
        destino = destino_libre(carpeta / fichero.name)

        if not simular:
            try:
                carpeta.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fichero, destino)
            except OSError as error:
                raise TareasError(
                    f"No se pudo copiar «{fichero.name}»: {error}"
                ) from error

        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Renombrar(Accion):
    """Cambia el nombre del fichero según una plantilla."""

    tipo = "renombrar"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._reservados: set[Path] = set()

    def ejecutar(self, ficheros: list[Path], simular: bool) -> list[Resultado]:
        self._reservados.clear()
        return super().ejecutar(ficheros, simular)

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        try:
            fecha = datetime.fromtimestamp(fichero.stat().st_mtime)
        except OSError as error:
            raise TareasError(
                f"No se pudo leer la fecha de «{fichero.name}»: {error}"
            ) from error

        try:
            nuevo_nombre = self.config["plantilla"].format(
                fecha=fecha,
                n=n,
                ext=fichero.suffix.lower(),
                nombre=fichero.stem,
            )
        except (KeyError, ValueError) as error:
            raise TareasError(
                f"La plantilla «{self.config['plantilla']}» no es válida: {error}"
            ) from error

        if nuevo_nombre == fichero.name:
            return Resultado(fichero, None, "saltado")

        try:
            candidato = fichero.with_name(nuevo_nombre)
        except ValueError as error:
            raise TareasError(
                f"El nombre generado «{nuevo_nombre}» no es válido: {error}"
            ) from error

        destino = destino_libre(candidato, self._reservados)
        self._reservados.add(destino)

        if not simular:
            try:
                fichero.rename(destino)
            except OSError as error:
                raise TareasError(
                    f"No se pudo renombrar «{fichero.name}»: {error}"
                ) from error

        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Borrar(Accion):
    """Borra el fichero. Es destructiva y pide confirmación."""

    tipo = "borrar"
    destructiva = True

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        if not simular:
            try:
                fichero.unlink()
            except OSError as error:
                raise TareasError(
                    f"No se pudo borrar «{fichero.name}»: {error}"
                ) from error

        return Resultado(fichero, None, "simulado" if simular else "hecho")
