"""Carga y validación del fichero acciones.json."""

import json
import re
from pathlib import Path

from tareas.errores import AccionNoValida, ConfigError

TIPOS = {"mover", "copiar", "renombrar", "borrar"}
CAMPOS_ACCION = {
    "nombre",
    "descripcion",
    "tipo",
    "origen",
    "destino",
    "filtro",
    "plantilla",
}
CAMPOS_FILTRO = {
    "extensiones",
    "patron",
    "mas_antiguo_que_dias",
    "mayor_que_mb",
}
POR_TIPO = {"mover": "destino", "copiar": "destino", "renombrar": "plantilla"}


def _texto_obligatorio(nombre: str, campo: str, valor: object) -> str:
    """Comprueba que un campo es texto no vacío y lo devuelve limpio."""
    if not isinstance(valor, str) or not valor.strip():
        raise AccionNoValida(nombre, campo, "es obligatorio y debe ser texto")
    return valor.strip()


def _validar_filtro(nombre: str, filtro: object) -> None:
    """Valida el objeto opcional «filtro» de una acción."""
    if filtro is None:
        return
    if not isinstance(filtro, dict):
        raise AccionNoValida(nombre, "filtro", "debe ser un objeto JSON")

    desconocidos = set(filtro) - CAMPOS_FILTRO
    if desconocidos:
        raise AccionNoValida(
            nombre,
            "filtro",
            f"campos desconocidos: {', '.join(sorted(desconocidos))}",
        )

    extensiones = filtro.get("extensiones")
    if extensiones is not None:
        if not isinstance(extensiones, list) or not extensiones:
            raise AccionNoValida(
                nombre,
                "filtro.extensiones",
                "debe ser una lista no vacía",
            )
        for extension in extensiones:
            if (
                not isinstance(extension, str)
                or not extension.startswith(".")
                or len(extension) < 2
            ):
                raise AccionNoValida(
                    nombre,
                    "filtro.extensiones",
                    f"«{extension}» debe empezar por punto (ejemplo: .pdf)",
                )

    patron = filtro.get("patron")
    if patron is not None:
        if not isinstance(patron, str) or not patron:
            raise AccionNoValida(
                nombre,
                "filtro.patron",
                "debe ser una expresión regular no vacía",
            )
        try:
            re.compile(patron)
        except re.error as error:
            raise AccionNoValida(
                nombre,
                "filtro.patron",
                f"expresión regular rota: {error}",
            ) from error

    dias = filtro.get("mas_antiguo_que_dias")
    if dias is not None:
        if isinstance(dias, bool) or not isinstance(dias, int) or dias < 0:
            raise AccionNoValida(
                nombre,
                "filtro.mas_antiguo_que_dias",
                "debe ser un entero mayor o igual que 0",
            )

    megas = filtro.get("mayor_que_mb")
    if megas is not None:
        if (
            isinstance(megas, bool)
            or not isinstance(megas, (int, float))
            or megas < 0
        ):
            raise AccionNoValida(
                nombre,
                "filtro.mayor_que_mb",
                "debe ser un número mayor o igual que 0",
            )


def _validar_accion(accion: object, indice: int, vistos: set[str]) -> None:
    """Valida una acción concreta y añade su nombre a los ya vistos."""
    if not isinstance(accion, dict):
        raise ConfigError(f"La acción número {indice} no es un objeto JSON")

    nombre = accion.get("nombre")
    if not isinstance(nombre, str) or not nombre.strip():
        raise AccionNoValida(f"nº {indice}", "nombre", "es obligatorio y debe ser texto")
    nombre = nombre.strip()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", nombre):
        raise AccionNoValida(
            nombre,
            "nombre",
            "debe estar en minúsculas y usar guiones (ejemplo: mover-entregas)",
        )
    if nombre in vistos:
        raise AccionNoValida(nombre, "nombre", "está repetido")
    vistos.add(nombre)

    _texto_obligatorio(nombre, "descripcion", accion.get("descripcion"))

    tipo = accion.get("tipo")
    if not isinstance(tipo, str) or tipo not in TIPOS:
        raise AccionNoValida(
            nombre,
            "tipo",
            f"«{tipo}» no existe; usa uno de: {', '.join(sorted(TIPOS))}",
        )

    desconocidos = set(accion) - CAMPOS_ACCION
    if desconocidos:
        raise AccionNoValida(
            nombre,
            "campos",
            f"desconocidos: {', '.join(sorted(desconocidos))}",
        )

    if "origen" in accion:
        _texto_obligatorio(nombre, "origen", accion.get("origen"))
    if "destino" in accion:
        _texto_obligatorio(nombre, "destino", accion.get("destino"))
    if "plantilla" in accion:
        _texto_obligatorio(nombre, "plantilla", accion.get("plantilla"))

    _validar_filtro(nombre, accion.get("filtro"))

    campo_extra = POR_TIPO.get(tipo)
    if campo_extra and not accion.get(campo_extra):
        raise AccionNoValida(
            nombre,
            campo_extra,
            f"es obligatorio en acciones de tipo {tipo}",
        )


def cargar(ruta: Path) -> list[dict]:
    """Lee acciones.json y devuelve la lista de acciones ya validada."""
    ruta = Path(ruta).expanduser()

    if not ruta.is_file():
        raise ConfigError(
            f"No encuentro «{ruta}». Crea acciones.json o usa --config RUTA."
        )

    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as error:
        raise ConfigError(f"No puedo leer «{ruta}»: {error}") from error

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise ConfigError(
            f"{ruta.name} no es JSON válido: "
            f"línea {error.lineno}, columna {error.colno} ({error.msg})"
        ) from error

    if not isinstance(datos, dict):
        raise ConfigError(
            f"{ruta.name} debe contener un objeto JSON con «version» y «acciones»."
        )

    version = datos.get("version")
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise ConfigError(
            f"Versión de esquema no soportada: {version!r}. Usa \"version\": 1."
        )

    acciones = datos.get("acciones")
    if not isinstance(acciones, list) or not acciones:
        raise ConfigError("Falta la lista «acciones» o está vacía.")

    vistos: set[str] = set()
    for indice, accion in enumerate(acciones, start=1):
        _validar_accion(accion, indice, vistos)

    return acciones
