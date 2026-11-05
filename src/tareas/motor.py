"""Selección de ficheros y ejecución de acciones."""

import re
import time
from pathlib import Path

from tareas.acciones import Accion, Resultado
from tareas.errores import TareasError


class Motor:
    """Recibe las acciones validadas y las ejecuta sobre una carpeta."""

    def __init__(self, acciones: list[dict]) -> None:
        self.acciones = {
            accion["nombre"]: Accion.desde_config(accion) for accion in acciones
        }

    @staticmethod
    def seleccionar(carpeta: Path, filtro: dict) -> list[Path]:
        """Devuelve los ficheros de la carpeta que cumplen el filtro."""
        extensiones = {extension.lower() for extension in filtro.get("extensiones", [])}
        patron = re.compile(filtro["patron"]) if filtro.get("patron") else None
        dias = filtro.get("mas_antiguo_que_dias")
        megas = filtro.get("mayor_que_mb")
        ahora = time.time()

        try:
            entradas = sorted(carpeta.iterdir(), key=lambda ruta: ruta.name.lower())
        except OSError as error:
            raise TareasError(
                f"No puedo leer la carpeta «{carpeta}»: {error}"
            ) from error

        elegidos: list[Path] = []
        for fichero in entradas:
            try:
                if not fichero.is_file():
                    continue
                if extensiones and fichero.suffix.lower() not in extensiones:
                    continue
                if patron and not patron.search(fichero.name):
                    continue

                if dias or megas:
                    datos = fichero.stat()
                    if dias and ahora - datos.st_mtime < dias * 86400:
                        continue
                    if megas and datos.st_size < megas * 1024 * 1024:
                        continue
            except OSError:
                # Enlace roto, fichero sin permisos o desaparecido: lo saltamos.
                continue

            elegidos.append(fichero)

        return elegidos

    def ejecutar(
        self,
        nombre: str,
        carpeta: Path | None,
        simular: bool,
    ) -> list[Resultado]:
        """Ejecuta una acción por su nombre sobre una carpeta."""
        accion = self.acciones.get(nombre)
        if accion is None:
            raise TareasError(
                f"No hay ninguna acción «{nombre}». "
                "Mira la lista con: tareas acciones"
            )

        ruta = (carpeta or Path(accion.config.get("origen", "."))).expanduser()
        if not ruta.is_dir():
            raise TareasError(f"La carpeta «{ruta}» no existe o no es una carpeta.")

        filtro = accion.config.get("filtro") or {}
        ficheros = self.seleccionar(ruta, filtro)
        return accion.ejecutar(ficheros, simular)
