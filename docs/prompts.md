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

## Semana 3 · dos acciones nuevas y pytest (2026-11-06)

**Herramienta:** OpenCode en modo Build.
**Prompt del plan:** «Lee @AGENTS.md y @acciones.json. Quiero llegar a 5 acciones: añade `mover-instaladores` y `borrar-temporales`, y una batería de pruebas con pytest para configuración, acciones, motor y CLI».
**Qué corregí del plan:** `mover-instaladores` reutiliza el tipo `mover` y solo necesita una entrada nueva en el JSON; `borrar-temporales` usa el tipo `borrar` existente y mantiene la confirmación salvo `--si`. Las pruebas debían usar `tmp_path` para no tocar nunca `pruebas-tareas` ni carpetas reales.
**Diffs rechazados o cambiados:** un test de `destino_libre` esperaba el sufijo `(2)` sin reservar el nombre original; corregí el test, no el código. No añadí tipos nuevos ni dependencias de ejecución: `pytest` queda como dependencia de desarrollo.
**Qué aprendí:** `tmp_path` aísla cada prueba; `CliRunner` permite comprobar códigos de salida, la simulación y la respuesta `n` a la confirmación; una acción nueva de un tipo existente solo toca `acciones.json`. La batería completa suma 63 pruebas.

## Semana 3 · IA con Gemini (2026-11-06)

**Herramienta:** OpenCode en modo Build.
**Prompt del plan:** «Lee @AGENTS.md y @src/tareas/cli.py. Quiero añadir `tareas explicar NOMBRE [CARPETA]` con Gemini para explicar qué haría una acción sin ejecutarla. La clave debe ir en `GEMINI_API_KEY` y no quiero añadir dependencias de ejecución».
**Qué corregí del plan:** la IA no debía decidir ni ejecutar ficheros, solo explicar. La petición se construye con la configuración de la acción y los nombres de los ficheros, nunca con su contenido. Puse el proveedor detrás de un `Protocol` y un proveedor falso en las pruebas para no gastar cuota.
**Diffs rechazados o cambiados:** empecé con `generateContent` y `gemini-2.5-flash`, pero Google devolvía 404 para cuentas nuevas; `gemini-3.8-flash` daba 503 por alta demanda y `gemini-3.5-flash` se quedaba sin tokens pensando. Migré a la Interactions API (`POST /v1beta/interactions`) con `thinking_level: "low"` y dejé `gemini-flash-lite-latest` como modelo por defecto. También descarté añadir el SDK `google-genai`: con `urllib` no hay dependencias nuevas.
**Qué aprendí:** los modelos con razonamiento pueden gastar el presupuesto en pensamientos y devolver texto vacío; hay que leer los pasos `model_output`, no `candidates`. Una prueba real de IA no debe ejecutarse en pytest: se inyecta un proveedor falso y la llamada real se hace a mano con `--config` sobre `pruebas-tareas`. La explicación se apoya en una simulación sin efectos para conocer los nombres finales. La batería completa suma 89 pruebas.
