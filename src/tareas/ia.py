"""Proveedor de IA para explicar acciones sin ejecutarlas."""

import http.client
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol

from tareas.acciones import Resultado
from tareas.errores import ConfigError, TareasError

MODELO_POR_DEFECTO = "gemini-flash-lite-latest"
URL_API = "https://generativelanguage.googleapis.com/v1beta/interactions"
MAX_FICHEROS_EN_PETICION = 100


class ProveedorIA(Protocol):
    """Interfaz mínima que debe cumplir un proveedor de IA."""

    def explicar(self, peticion: str) -> str:
        """Devuelve una explicación en texto a partir de una petición."""


class Gemini:
    """Proveedor que llama a la API de Google Gemini."""

    def __init__(
        self,
        clave: str,
        modelo: str = MODELO_POR_DEFECTO,
        timeout: float = 60.0,
    ) -> None:
        self.clave = clave
        self.modelo = modelo.removeprefix("models/")
        self.timeout = timeout

    def explicar(self, peticion: str) -> str:
        """Envía la petición a Gemini y devuelve el texto generado."""
        cuerpo = {
            "model": self.modelo,
            "input": peticion,
            "generation_config": {
                "thinking_level": "low",
                "max_output_tokens": 1024,
            },
        }
        respuesta = self._enviar(cuerpo)
        return self._leer_texto(respuesta)

    def _enviar(self, cuerpo: dict) -> dict:
        """Hace la petición HTTP y devuelve el JSON de respuesta."""
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        peticion = urllib.request.Request(
            URL_API,
            data=datos,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "tareas/0.1.0",
                "x-goog-api-key": self.clave,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout) as respuesta:
                resultado = json.loads(respuesta.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise TareasError(
                f"Gemini respondió con error {error.code}: {_detalle_error(error)}"
            ) from error
        except urllib.error.URLError as error:
            raise TareasError(
                f"No puedo conectar con Gemini: {error.reason}"
            ) from error
        except TimeoutError as error:
            raise TareasError("Gemini tardó demasiado en responder.") from error
        except (http.client.HTTPException, OSError) as error:
            raise TareasError(
                f"Se cortó la conexión con Gemini: {error}"
            ) from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TareasError(
                "Gemini devolvió una respuesta que no puedo leer."
            ) from error

        if not isinstance(resultado, dict):
            raise TareasError("Gemini devolvió una respuesta que no puedo leer.")
        return resultado

    @staticmethod
    def _leer_texto(respuesta: dict) -> str:
        """Extrae el texto de los pasos «model_output» de la respuesta."""
        estado = respuesta.get("status")
        if isinstance(estado, str) and estado in {"failed", "cancelled"}:
            raise TareasError(
                f"Gemini no pudo completar la petición: {_detalle_estado(respuesta)}"
            )
        if estado == "incomplete":
            raise TareasError(
                "Gemini se quedó sin tokens antes de terminar la explicación."
            )

        pasos = respuesta.get("steps")
        if not isinstance(pasos, list) or not pasos:
            raise TareasError("Gemini no devolvió ninguna respuesta.")

        textos: list[str] = []
        for paso in pasos:
            if not isinstance(paso, dict) or paso.get("type") != "model_output":
                continue
            contenido_paso = paso.get("content")
            if not isinstance(contenido_paso, list):
                continue
            for contenido in contenido_paso:
                if not isinstance(contenido, dict):
                    continue
                if contenido.get("type") != "text":
                    continue
                texto = contenido.get("text")
                if isinstance(texto, str) and texto.strip():
                    textos.append(texto.strip())

        texto_final = "\n".join(textos).strip()
        if not texto_final:
            raise TareasError("Gemini devolvió una respuesta vacía.")
        return texto_final


def _detalle_error(error: urllib.error.HTTPError) -> str:
    """Intenta leer el mensaje de error que devuelve Google."""
    try:
        datos = json.loads(error.read().decode("utf-8"))
    except (
        AttributeError,
        http.client.HTTPException,
        OSError,
        ValueError,
    ):
        return "sin detalle"

    if isinstance(datos, dict):
        detalle = datos.get("error")
        if isinstance(detalle, dict):
            mensaje = detalle.get("message")
            if isinstance(mensaje, str) and mensaje:
                return mensaje
    return "sin detalle"


def _detalle_estado(respuesta: dict) -> str:
    """Busca el primer mensaje de error de una interacción fallida."""
    errores = respuesta.get("errors")
    if isinstance(errores, list):
        for error in errores:
            if isinstance(error, dict) and error.get("message"):
                return str(error["message"])
    return str(respuesta.get("status") or "sin detalle")


def crear_proveedor() -> ProveedorIA:
    """Crea el proveedor de IA a partir de las variables de entorno."""
    clave = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not clave:
        raise ConfigError(
            "Falta la variable de entorno GEMINI_API_KEY. "
            "Crea una clave en https://aistudio.google.com/app/apikey y guárdala "
            'con setx GEMINI_API_KEY "tu_clave" en Windows o '
            'export GEMINI_API_KEY="tu_clave" en Linux y macOS.'
        )

    modelo = (os.environ.get("GEMINI_MODELO") or "").strip()
    return Gemini(clave, modelo or MODELO_POR_DEFECTO)


def _nombre_seguro(nombre: str) -> str:
    """Quita caracteres de control para que un nombre no altere la petición."""
    limpio = "".join(
        caracter if caracter.isprintable() else " " for caracter in nombre
    )
    return limpio.strip()


def _lineas_plan(resultados: list[Resultado]) -> list[str]:
    """Describe una simulación de la acción, sin tocar el disco."""
    lineas = ["Plan calculado sin ejecutar (no se ha modificado nada):"]
    for resultado in resultados[:MAX_FICHEROS_EN_PETICION]:
        origen = _nombre_seguro(resultado.origen.name)
        if resultado.destino is None:
            if resultado.estado == "saltado":
                lineas.append(f"- {origen}: se quedaría igual")
            else:
                lineas.append(f"- {origen}: se borraría")
        else:
            destino = _nombre_seguro(resultado.destino.name)
            lineas.append(f"- {origen} -> {destino}")
    if len(resultados) > MAX_FICHEROS_EN_PETICION:
        lineas.append(
            f"- … y {len(resultados) - MAX_FICHEROS_EN_PETICION} ficheros más"
        )
    return lineas


def crear_peticion(
    accion: dict,
    carpeta: Path,
    ficheros: list[Path],
    resultados: list[Resultado] | None = None,
) -> str:
    """Construye la petición con la acción y los nombres, sin leer contenidos."""
    seleccionados = ficheros[:MAX_FICHEROS_EN_PETICION]
    nombres = "\n".join(
        f"- {_nombre_seguro(fichero.name)}" for fichero in seleccionados
    )
    if not nombres:
        nombres = "- (ninguno)"
    elif len(ficheros) > MAX_FICHEROS_EN_PETICION:
        nombres += (
            f"\n- … y {len(ficheros) - MAX_FICHEROS_EN_PETICION} ficheros más"
        )

    lineas = [
        "Eres un asistente que explica acciones de una CLI de gestión de ficheros.",
        "Responde en español, en 2 o 3 frases claras y en texto plano, sin Markdown.",
        "No ejecutes nada y no inventes ficheros ni rutas que no aparezcan aquí.",
        "",
        f"Acción: {accion['nombre']}",
        f"Descripción: {accion['descripcion']}",
        f"Tipo: {accion['tipo']}",
        f"Carpeta: {carpeta}",
    ]
    if "destino" in accion:
        lineas.append(f"Destino: {accion['destino']}")
    if "plantilla" in accion:
        lineas.append(f"Plantilla de nombre: {accion['plantilla']}")
    if "filtro" in accion:
        filtro = json.dumps(accion["filtro"], ensure_ascii=False)
        lineas.append(f"Filtro: {filtro}")
    lineas.append(f"Ficheros seleccionados ({len(ficheros)}):")
    lineas.append(nombres)
    if resultados:
        lineas.extend(_lineas_plan(resultados))
    lineas.append("")
    lineas.append(
        "Explica qué haría esta acción con estos ficheros. "
        "Si hay un plan simulado, usa los nombres de destino que aparecen en él."
    )
    return "\n".join(lineas)
