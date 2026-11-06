# Prompts clave

## Orden version (plan → build)
Prompt: Lee @AGENTS.md y @src/tareas/__init__.py. Quiero crear src/tareas/cli.py con una app de Typer y la orden «version»...
Resultado: añadió __version__ en __init__.py, creó cli.py y un callback vacío para que version siga siendo subcomando.

## Semana 1 y 2 · listar, acciones.json y motor (2026-11-06)

**Herramienta:** OpenCode 2.2.5.
**Prompt del plan:** «Lee @AGENTS.md y @src/tareas/cli.py. Quiero añadir la orden listar [CARPETA]...».
**Qué corregí del plan:** seguí el criterio del profesor: `listar` incluye carpetas y las pone primero; el listado de acciones pasa a llamarse `acciones`; las pruebas se hacen en `pruebas-tareas` y con `--simular`.
**Diffs rechazados o cambiados:** sustituí el símbolo `✔` por `OK:` porque la consola Windows cp1252 lanzaba `UnicodeEncodeError`; mantuve `pathlib`, `shutil` y Rich, sin dependencias nuevas.
**Qué aprendí:** Typer convierte el argumento a `Path`; `--simular` no debe llamar a `mkdir`, `move`, `rename` ni `unlink`; Rich necesita `escape` para que los nombres con corchetes salgan enteros.