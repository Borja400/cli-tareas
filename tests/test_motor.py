"""Pruebas de la selección de ficheros y de la ejecución del motor."""

import os
import time
from pathlib import Path

import pytest

from tareas.errores import TareasError
from tareas.motor import Motor


def config_mover(origen: Path, destino: Path) -> dict:
    return {
        "nombre": "mover-x",
        "descripcion": "Mueve PDF",
        "tipo": "mover",
        "origen": str(origen),
        "filtro": {"extensiones": [".pdf"]},
        "destino": str(destino),
    }


def test_seleccionar_por_extension(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "c.PDF").write_text("c", encoding="utf-8")
    (tmp_path / "carpeta").mkdir()

    elegidos = Motor.seleccionar(tmp_path, {"extensiones": [".pdf"]})

    assert [fichero.name for fichero in elegidos] == ["a.pdf", "c.PDF"]


def test_seleccionar_por_patron(tmp_path: Path) -> None:
    for nombre in ("entrega.pdf", "tarea.pdf", "otro.pdf"):
        (tmp_path / nombre).write_text("x", encoding="utf-8")

    elegidos = Motor.seleccionar(
        tmp_path, {"patron": "(?i)(entrega|tarea)"}
    )

    assert [fichero.name for fichero in elegidos] == ["entrega.pdf", "tarea.pdf"]


def test_seleccionar_por_antiguedad(tmp_path: Path) -> None:
    viejo = tmp_path / "viejo.pdf"
    nuevo = tmp_path / "nuevo.pdf"
    viejo.write_text("viejo", encoding="utf-8")
    nuevo.write_text("nuevo", encoding="utf-8")
    hace_diez_dias = time.time() - 10 * 86400
    os.utime(viejo, (hace_diez_dias, hace_diez_dias))

    elegidos = Motor.seleccionar(
        tmp_path, {"mas_antiguo_que_dias": 5}
    )

    assert [fichero.name for fichero in elegidos] == ["viejo.pdf"]


def test_seleccionar_por_tamano(tmp_path: Path) -> None:
    grande = tmp_path / "grande.bin"
    pequeno = tmp_path / "pequeno.bin"
    grande.write_bytes(b"x" * (2 * 1024 * 1024))
    pequeno.write_bytes(b"x" * 10)

    elegidos = Motor.seleccionar(tmp_path, {"mayor_que_mb": 1})

    assert [fichero.name for fichero in elegidos] == ["grande.bin"]


def test_seleccionar_carpeta_inexistente(tmp_path: Path) -> None:
    with pytest.raises(TareasError) as error:
        Motor.seleccionar(tmp_path / "no-existe", {})

    assert "No puedo leer" in str(error.value)


def test_motor_ejecuta_mover(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("contenido", encoding="utf-8")
    motor = Motor([config_mover(origen, destino)])

    resultados = motor.ejecutar("mover-x", None, False)

    assert len(resultados) == 1
    assert resultados[0].estado == "hecho"
    assert (destino / "entrega.pdf").is_file()


def test_motor_simula_sin_tocar_el_disco(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("contenido", encoding="utf-8")
    motor = Motor([config_mover(origen, destino)])

    resultados = motor.ejecutar("mover-x", origen, True)

    assert resultados[0].estado == "simulado"
    assert fichero.is_file()
    assert not destino.exists()


def test_motor_accion_inexistente(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    origen.mkdir()
    motor = Motor([config_mover(origen, tmp_path / "destino")])

    with pytest.raises(TareasError) as error:
        motor.ejecutar("no-existe", origen, True)

    assert "No hay ninguna acción" in str(error.value)


def test_motor_carpeta_inexistente(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    origen.mkdir()
    motor = Motor([config_mover(origen, tmp_path / "destino")])

    with pytest.raises(TareasError) as error:
        motor.ejecutar("mover-x", tmp_path / "no-existe", True)

    assert "no existe" in str(error.value)


def test_preparar_no_ejecuta_la_accion(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("contenido", encoding="utf-8")
    motor = Motor([config_mover(origen, destino)])

    accion, ruta, ficheros = motor.preparar("mover-x", None)

    assert accion.nombre == "mover-x"
    assert ruta == origen
    assert [seleccionado.name for seleccionado in ficheros] == ["entrega.pdf"]
    assert fichero.is_file()
    assert not destino.exists()
