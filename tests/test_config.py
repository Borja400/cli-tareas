"""Pruebas de la carga y validación de acciones.json."""

import json
from pathlib import Path

import pytest

from tareas.config import cargar
from tareas.errores import AccionNoValida, ConfigError


def escribir(tmp_path: Path, datos: object) -> Path:
    """Escribe un acciones.json temporal y devuelve su ruta."""
    ruta = tmp_path / "acciones.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return ruta


def accion_copiar(**cambios: object) -> dict:
    """Acción válida de ejemplo, con posibilidad de cambiar campos."""
    accion = {
        "nombre": "copiar-apuntes",
        "descripcion": "Copia los apuntes",
        "tipo": "copiar",
        "origen": "~/Documentos/Apuntes",
        "destino": "~/Documentos/Copia-apuntes",
        "filtro": {"extensiones": [".pdf", ".docx"]},
    }
    accion.update(cambios)
    return accion


def test_carga_config_valida(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, {"version": 1, "acciones": [accion_copiar()]})

    acciones = cargar(ruta)

    assert len(acciones) == 1
    assert acciones[0]["nombre"] == "copiar-apuntes"


def test_archivo_inexistente(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as error:
        cargar(tmp_path / "no-existe.json")

    assert error.value.codigo_salida == 3
    assert "No encuentro" in str(error.value)


def test_json_roto(tmp_path: Path) -> None:
    ruta = tmp_path / "acciones.json"
    ruta.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigError) as error:
        cargar(ruta)

    assert "no es JSON válido" in str(error.value)


def test_raiz_no_es_objeto(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, [])

    with pytest.raises(ConfigError) as error:
        cargar(ruta)

    assert "objeto JSON" in str(error.value)


def test_version_incorrecta(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, {"version": 2, "acciones": [accion_copiar()]})

    with pytest.raises(ConfigError) as error:
        cargar(ruta)

    assert "Versión de esquema" in str(error.value)


def test_version_decimal_no_vale(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, {"version": 1.0, "acciones": [accion_copiar()]})

    with pytest.raises(ConfigError) as error:
        cargar(ruta)

    assert "Versión de esquema" in str(error.value)


def test_version_booleana_no_vale(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, {"version": True, "acciones": [accion_copiar()]})

    with pytest.raises(ConfigError) as error:
        cargar(ruta)

    assert "Versión de esquema" in str(error.value)


def test_lista_de_acciones_vacia(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, {"version": 1, "acciones": []})

    with pytest.raises(ConfigError) as error:
        cargar(ruta)

    assert "acciones" in str(error.value)


def test_accion_no_es_objeto(tmp_path: Path) -> None:
    ruta = escribir(tmp_path, {"version": 1, "acciones": ["hola"]})

    with pytest.raises(ConfigError) as error:
        cargar(ruta)

    assert "no es un objeto JSON" in str(error.value)


def test_nombre_repetido(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {"version": 1, "acciones": [accion_copiar(), accion_copiar()]},
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "está repetido" in str(error.value)


def test_nombre_con_mayusculas_o_espacios(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {"version": 1, "acciones": [accion_copiar(nombre="Copiar Apuntes")]},
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "minúsculas" in str(error.value)


def test_tipo_desconocido(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {"version": 1, "acciones": [accion_copiar(tipo="comprimir")]},
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "tipo" in str(error.value)


def test_mover_sin_destino(tmp_path: Path) -> None:
    accion = accion_copiar(tipo="mover")
    del accion["destino"]
    ruta = escribir(tmp_path, {"version": 1, "acciones": [accion]})

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "destino" in str(error.value)


def test_renombrar_sin_plantilla(tmp_path: Path) -> None:
    accion = {
        "nombre": "renombrar-x",
        "descripcion": "Renombra",
        "tipo": "renombrar",
    }
    ruta = escribir(tmp_path, {"version": 1, "acciones": [accion]})

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "plantilla" in str(error.value)


def test_extension_sin_punto(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {
            "version": 1,
            "acciones": [accion_copiar(filtro={"extensiones": ["pdf"]})],
        },
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "filtro.extensiones" in str(error.value)


def test_extensiones_vacias(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {
            "version": 1,
            "acciones": [accion_copiar(filtro={"extensiones": []})],
        },
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "lista no vacía" in str(error.value)


def test_patron_invalido(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {
            "version": 1,
            "acciones": [accion_copiar(filtro={"patron": "("})],
        },
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "expresión regular rota" in str(error.value)


def test_dias_negativos(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {
            "version": 1,
            "acciones": [
                accion_copiar(filtro={"mas_antiguo_que_dias": -1})
            ],
        },
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "entero mayor o igual" in str(error.value)


def test_megas_booleanas_no_valen(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {
            "version": 1,
            "acciones": [accion_copiar(filtro={"mayor_que_mb": True})],
        },
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "número mayor o igual" in str(error.value)


def test_campo_desconocido(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        {
            "version": 1,
            "acciones": [accion_copiar(confirmar=True)],
        },
    )

    with pytest.raises(AccionNoValida) as error:
        cargar(ruta)

    assert "desconocidos: confirmar" in str(error.value)
