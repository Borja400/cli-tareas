"""Pruebas de las acciones sobre ficheros de una carpeta temporal."""

import os
from datetime import datetime
from pathlib import Path

import pytest

from tareas.acciones import Borrar, Copiar, Mover, Renombrar, destino_libre
from tareas.errores import TareasError


def config_mover(destino: Path) -> dict:
    return {
        "nombre": "mover-x",
        "descripcion": "Mueve ficheros",
        "tipo": "mover",
        "destino": str(destino),
    }


def config_copiar(destino: Path) -> dict:
    return {
        "nombre": "copiar-x",
        "descripcion": "Copia ficheros",
        "tipo": "copiar",
        "destino": str(destino),
    }


def config_renombrar(plantilla: str) -> dict:
    return {
        "nombre": "renombrar-x",
        "descripcion": "Renombra ficheros",
        "tipo": "renombrar",
        "plantilla": plantilla,
    }


def config_borrar() -> dict:
    return {
        "nombre": "borrar-x",
        "descripcion": "Borra ficheros",
        "tipo": "borrar",
    }


def test_destino_libre_sin_colision(tmp_path: Path) -> None:
    destino = tmp_path / "fichero.txt"

    assert destino_libre(destino) == destino


def test_destino_libre_con_colisiones(tmp_path: Path) -> None:
    destino = tmp_path / "fichero.txt"
    destino.write_text("original", encoding="utf-8")
    (tmp_path / "fichero (1).txt").write_text("otro", encoding="utf-8")

    libre = destino_libre(destino)

    assert libre.name == "fichero (2).txt"
    assert not libre.exists()


def test_destino_libre_respeta_reservados(tmp_path: Path) -> None:
    destino = tmp_path / "fichero.txt"
    reservados = {destino, tmp_path / "fichero (1).txt"}

    libre = destino_libre(destino, reservados)

    assert libre.name == "fichero (2).txt"


def test_mover_fichero(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("contenido", encoding="utf-8")

    resultado = Mover(config_mover(destino)).aplicar(fichero, 1, False)

    assert resultado.estado == "hecho"
    assert resultado.destino == destino / "entrega.pdf"
    assert not fichero.exists()
    assert (destino / "entrega.pdf").read_text(encoding="utf-8") == "contenido"


def test_mover_simular_no_toca_el_disco(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("contenido", encoding="utf-8")

    resultado = Mover(config_mover(destino)).aplicar(fichero, 1, True)

    assert resultado.estado == "simulado"
    assert fichero.is_file()
    assert not destino.exists()


def test_mover_no_sobrescribe(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    destino.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("nuevo", encoding="utf-8")
    existente = destino / "entrega.pdf"
    existente.write_text("existente", encoding="utf-8")

    resultado = Mover(config_mover(destino)).aplicar(fichero, 1, False)

    assert resultado.destino == destino / "entrega (1).pdf"
    assert existente.read_text(encoding="utf-8") == "existente"
    assert (destino / "entrega (1).pdf").read_text(encoding="utf-8") == "nuevo"


def test_copiar_fichero(tmp_path: Path) -> None:
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("contenido", encoding="utf-8")
    destino = tmp_path / "copia"

    resultado = Copiar(config_copiar(destino)).aplicar(origen, 1, False)

    assert resultado.estado == "hecho"
    assert origen.is_file()
    assert (destino / "apuntes.pdf").read_text(encoding="utf-8") == "contenido"


def test_copiar_simular_no_toca_el_disco(tmp_path: Path) -> None:
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("contenido", encoding="utf-8")
    destino = tmp_path / "copia"

    resultado = Copiar(config_copiar(destino)).aplicar(origen, 1, True)

    assert resultado.estado == "simulado"
    assert origen.is_file()
    assert not destino.exists()


def test_renombrar_fichero(tmp_path: Path) -> None:
    fichero = tmp_path / "IMG_1234.jpg"
    fichero.write_text("foto", encoding="utf-8")

    resultado = Renombrar(config_renombrar("{nombre}-{n:03}{ext}")).aplicar(
        fichero, 7, False
    )

    assert resultado.estado == "hecho"
    assert resultado.destino == tmp_path / "IMG_1234-007.jpg"
    assert not fichero.exists()
    assert (tmp_path / "IMG_1234-007.jpg").is_file()


def test_renombrar_simular_no_toca_el_disco(tmp_path: Path) -> None:
    fichero = tmp_path / "IMG_1234.jpg"
    fichero.write_text("foto", encoding="utf-8")

    resultado = Renombrar(config_renombrar("{nombre}-{n:03}{ext}")).aplicar(
        fichero, 7, True
    )

    assert resultado.estado == "simulado"
    assert fichero.is_file()
    assert not (tmp_path / "IMG_1234-007.jpg").exists()


def test_renombrar_no_sobrescribe(tmp_path: Path) -> None:
    fichero = tmp_path / "IMG_1234.jpg"
    fichero.write_text("foto", encoding="utf-8")
    existente = tmp_path / "IMG_1234-007.jpg"
    existente.write_text("existente", encoding="utf-8")

    resultado = Renombrar(config_renombrar("{nombre}-{n:03}{ext}")).aplicar(
        fichero, 7, False
    )

    assert resultado.destino == tmp_path / "IMG_1234-007 (1).jpg"
    assert existente.read_text(encoding="utf-8") == "existente"
    assert (tmp_path / "IMG_1234-007 (1).jpg").is_file()


def test_renombrar_con_fecha(tmp_path: Path) -> None:
    fichero = tmp_path / "scan.png"
    fichero.write_text("escaneo", encoding="utf-8")
    momento = 1700000000
    os.utime(fichero, (momento, momento))
    esperado = datetime.fromtimestamp(momento).strftime("%Y-%m-%d") + ".png"

    resultado = Renombrar(config_renombrar("{fecha:%Y-%m-%d}{ext}")).aplicar(
        fichero, 1, False
    )

    assert resultado.destino is not None
    assert resultado.destino.name == esperado


def test_renombrar_mismo_nombre_se_salta(tmp_path: Path) -> None:
    fichero = tmp_path / "scan.png"
    fichero.write_text("escaneo", encoding="utf-8")

    resultado = Renombrar(config_renombrar("{nombre}{ext}")).aplicar(
        fichero, 1, False
    )

    assert resultado.estado == "saltado"
    assert resultado.destino is None
    assert fichero.is_file()


def test_renombrar_plantilla_invalida(tmp_path: Path) -> None:
    fichero = tmp_path / "scan.png"
    fichero.write_text("escaneo", encoding="utf-8")

    with pytest.raises(TareasError) as error:
        Renombrar(config_renombrar("{desconocido}")).aplicar(fichero, 1, False)

    assert "no es válida" in str(error.value)


def test_borrar_fichero(tmp_path: Path) -> None:
    fichero = tmp_path / "basura.tmp"
    fichero.write_text("temporal", encoding="utf-8")

    resultado = Borrar(config_borrar()).aplicar(fichero, 1, False)

    assert resultado.estado == "hecho"
    assert not fichero.exists()


def test_borrar_simular_no_toca_el_disco(tmp_path: Path) -> None:
    fichero = tmp_path / "basura.tmp"
    fichero.write_text("temporal", encoding="utf-8")

    resultado = Borrar(config_borrar()).aplicar(fichero, 1, True)

    assert resultado.estado == "simulado"
    assert fichero.is_file()
