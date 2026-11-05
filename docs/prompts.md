# Prompts clave

## Orden version (plan → build)
Prompt: Lee @AGENTS.md y @src/tareas/__init__.py. Quiero crear src/tareas/cli.py con una app de Typer y la orden «version»...
Resultado: añadió __version__ en __init__.py, creó cli.py y un callback vacío para que version siga siendo subcomando.