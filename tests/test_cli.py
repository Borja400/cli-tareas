"""Pruebas de las órdenes de la CLI con Typer."""

import json
from pathlib import Path

from typer.testing import CliRunner

from tareas.cli import app

runner = CliRunner()


def escribir_config(tmp_path: Path, acciones: list[dict]) -> Path:
    ruta = tmp_path / "acciones.json"
    ruta.write_text(
        json.dumps({"version": 1, "acciones": acciones}, ensure_ascii=False),
        encoding="utf-8",
    )
    return ruta


def accion_mover(origen: Path, destino: Path) -> dict:
    return {
        "nombre": "mover-x",
        "descripcion": "Mueve PDF",
        "tipo": "mover",
        "origen": str(origen),
        "filtro": {"extensiones": [".pdf"]},
        "destino": str(destino),
    }


def accion_borrar(origen: Path) -> dict:
    return {
        "nombre": "borrar-x",
        "descripcion": "Borra TMP",
        "tipo": "borrar",
        "origen": str(origen),
        "filtro": {"extensiones": [".tmp"]},
    }


def texto(resultado) -> str:
    """Une stdout y stderr, según la versión de Click."""
    return (resultado.output or "") + (getattr(resultado, "stderr", "") or "")


def test_version() -> None:
    resultado = runner.invoke(app, ["version"])

    assert resultado.exit_code == 0
    assert "tareas 0.1.0" in texto(resultado)


def test_ayuda() -> None:
    resultado = runner.invoke(app, ["--help"])

    assert resultado.exit_code == 0
    salida = texto(resultado)
    assert "listar" in salida
    assert "acciones" in salida
    assert "validar" in salida
    assert "ejecutar" in salida


def test_acciones(tmp_path: Path) -> None:
    config = escribir_config(
        tmp_path,
        [
            accion_mover(tmp_path / "origen", tmp_path / "destino"),
            accion_borrar(tmp_path / "origen"),
        ],
    )

    resultado = runner.invoke(
        app, ["--config", str(config), "acciones"]
    )

    assert resultado.exit_code == 0
    salida = texto(resultado)
    assert "mover-x" in salida
    assert "borrar-x" in salida


def test_validar_ok(tmp_path: Path) -> None:
    config = escribir_config(
        tmp_path,
        [accion_mover(tmp_path / "origen", tmp_path / "destino")],
    )

    resultado = runner.invoke(
        app, ["--config", str(config), "validar"]
    )

    assert resultado.exit_code == 0
    assert "acciones válidas" in texto(resultado)


def test_validar_json_roto(tmp_path: Path) -> None:
    config = tmp_path / "acciones.json"
    config.write_text("{", encoding="utf-8")

    resultado = runner.invoke(
        app, ["--config", str(config), "validar"]
    )

    assert resultado.exit_code == 3
    assert "no es JSON válido" in texto(resultado)


def test_validar_version_incorrecta(tmp_path: Path) -> None:
    config = tmp_path / "acciones.json"
    config.write_text(
        json.dumps(
            {
                "version": 2,
                "acciones": [
                    accion_mover(tmp_path / "origen", tmp_path / "destino")
                ],
            }
        ),
        encoding="utf-8",
    )

    resultado = runner.invoke(
        app, ["--config", str(config), "validar"]
    )

    assert resultado.exit_code == 3
    assert "Versión de esquema" in texto(resultado)


def test_config_inexistente(tmp_path: Path) -> None:
    resultado = runner.invoke(
        app,
        ["--config", str(tmp_path / "no-existe.json"), "validar"],
    )

    assert resultado.exit_code == 3
    assert "No encuentro" in texto(resultado)


def test_listar(tmp_path: Path) -> None:
    carpeta = tmp_path / "contenido"
    carpeta.mkdir()
    (carpeta / "subcarpeta").mkdir()
    (carpeta / "fichero.txt").write_text("hola", encoding="utf-8")

    resultado = runner.invoke(app, ["listar", str(carpeta)])

    assert resultado.exit_code == 0
    salida = texto(resultado)
    assert "subcarpeta" in salida
    assert "carpeta" in salida
    assert "fichero.txt" in salida
    assert "—" in salida


def test_listar_vacio(tmp_path: Path) -> None:
    carpeta = tmp_path / "vacia"
    carpeta.mkdir()

    resultado = runner.invoke(app, ["listar", str(carpeta)])

    assert resultado.exit_code == 0
    assert "está vacía" in texto(resultado)


def test_listar_inexistente(tmp_path: Path) -> None:
    resultado = runner.invoke(
        app, ["listar", str(tmp_path / "no-existe")]
    )

    assert resultado.exit_code == 1
    assert "no existe" in texto(resultado)


def test_listar_archivo(tmp_path: Path) -> None:
    archivo = tmp_path / "fichero.txt"
    archivo.write_text("hola", encoding="utf-8")

    resultado = runner.invoke(app, ["listar", str(archivo)])

    assert resultado.exit_code == 1
    assert "no existe o no es una carpeta" in texto(resultado)


def test_ejecutar_simular(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("contenido", encoding="utf-8")
    config = escribir_config(
        tmp_path, [accion_mover(origen, destino)]
    )

    resultado = runner.invoke(
        app,
        [
            "--config",
            str(config),
            "ejecutar",
            "mover-x",
            str(origen),
            "--simular",
        ],
    )

    assert resultado.exit_code == 0
    assert "SIMULACIÓN" in texto(resultado)
    assert fichero.is_file()
    assert not destino.exists()


def test_ejecutar_mover(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    fichero = origen / "entrega.pdf"
    fichero.write_text("contenido", encoding="utf-8")
    config = escribir_config(
        tmp_path, [accion_mover(origen, destino)]
    )

    resultado = runner.invoke(
        app,
        ["--config", str(config), "ejecutar", "mover-x", str(origen)],
    )

    assert resultado.exit_code == 0
    assert not fichero.exists()
    assert (destino / "entrega.pdf").is_file()


def test_ejecutar_borrar_cancelado(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    origen.mkdir()
    fichero = origen / "basura.tmp"
    fichero.write_text("temporal", encoding="utf-8")
    config = escribir_config(tmp_path, [accion_borrar(origen)])

    resultado = runner.invoke(
        app,
        ["--config", str(config), "ejecutar", "borrar-x", str(origen)],
        input="n\n",
    )

    assert resultado.exit_code == 1
    assert "Operación cancelada" in texto(resultado)
    assert fichero.is_file()


def test_ejecutar_borrar_simular(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    origen.mkdir()
    fichero = origen / "basura.tmp"
    fichero.write_text("temporal", encoding="utf-8")
    config = escribir_config(tmp_path, [accion_borrar(origen)])

    resultado = runner.invoke(
        app,
        [
            "--config",
            str(config),
            "ejecutar",
            "borrar-x",
            str(origen),
            "--simular",
        ],
    )

    assert resultado.exit_code == 0
    assert "SIMULACIÓN" in texto(resultado)
    assert fichero.is_file()


def test_ejecutar_borrar_con_si(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    origen.mkdir()
    fichero = origen / "basura.tmp"
    fichero.write_text("temporal", encoding="utf-8")
    config = escribir_config(tmp_path, [accion_borrar(origen)])

    resultado = runner.invoke(
        app,
        [
            "--config",
            str(config),
            "ejecutar",
            "borrar-x",
            str(origen),
            "--si",
        ],
    )

    assert resultado.exit_code == 0
    assert not fichero.exists()


def test_ejecutar_accion_inexistente(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    origen.mkdir()
    config = escribir_config(
        tmp_path, [accion_mover(origen, tmp_path / "destino")]
    )

    resultado = runner.invoke(
        app,
        [
            "--config",
            str(config),
            "ejecutar",
            "no-existe",
            str(origen),
            "--simular",
        ],
    )

    assert resultado.exit_code == 1
    assert "No hay ninguna acción" in texto(resultado)


def test_ejecutar_carpeta_inexistente(tmp_path: Path) -> None:
    origen = tmp_path / "origen"
    origen.mkdir()
    config = escribir_config(
        tmp_path, [accion_mover(origen, tmp_path / "destino")]
    )

    resultado = runner.invoke(
        app,
        [
            "--config",
            str(config),
            "ejecutar",
            "mover-x",
            str(tmp_path / "no-existe"),
            "--simular",
        ],
    )

    assert resultado.exit_code == 1
    assert "no existe" in texto(resultado)
