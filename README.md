# tareas

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.
Construida con Python 3.12, Typer, Rich y `uv`, siguiendo el proyecto **CLI tareas con IA**.

## Spec (versión 0 · 06/11/2026)

1. **Problema:** pierdo tiempo organizando apuntes, entregas y fotos de clase entre Descargas, Documentos y el móvil.
2. **Para quién:** para mí (Borja, 1.º DAM) y para cualquier estudiante que quiera ordenar sus ficheros desde la terminal.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier carpeta.
4. **Órdenes de la semana 1:** `tareas --help`, `tareas version`, `tareas listar [CARPETA]`.
5. **Órdenes disponibles:** `tareas acciones`, `tareas validar`, `tareas ejecutar NOMBRE [CARPETA] --simular`, `tareas ejecutar NOMBRE [CARPETA] --si` y `tareas --config RUTA ...`.
6. **Mis 5 acciones:** `mover-entregas`, `mover-instaladores`, `renombrar-escaneos`, `copiar-apuntes` y `borrar-temporales`.
7. **Nunca hará:** borrar sin confirmación, tocar ficheros fuera de la carpeta indicada ni sobrescribir un fichero existente.
8. **Plataformas:** Linux primero; también Windows y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 error de uso · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (se completa en la semana 4).

## Instalación

Desde la raíz del repositorio:

```bash
uv sync
uv run tareas --help
```

Para instalarla como comando global:

```bash
uv tool install --editable .
tareas --help
```

## Uso

```bash
tareas --help
tareas version
tareas listar
tareas listar "~/pruebas-tareas"
tareas acciones
tareas validar
tareas ejecutar mover-entregas --simular
tareas ejecutar mover-instaladores "~/pruebas-tareas/Descargas" --simular
tareas ejecutar renombrar-escaneos "~/pruebas-tareas/fotos" --simular
tareas ejecutar borrar-temporales "~/pruebas-tareas/Descargas" --simular
tareas --config pruebas-tareas/acciones-pruebas.json validar
```

`listar` muestra nombre, tipo (extensión o «carpeta»), tamaño legible y fecha de modificación.
Las carpetas salen primero y después los ficheros por orden alfabético.

## Acciones incluidas

| Acción | Tipo | Qué hace |
|---|---|---|
| `mover-entregas` | `mover` | Mueve los PDF y DOCX de Descargas que parezcan entregas o tareas a `Documentos/DAM/Entregas`. |
| `mover-instaladores` | `mover` | Mueve los `.exe` y `.msi` de Descargas a `Descargas/Instaladores`. |
| `renombrar-escaneos` | `renombrar` | Renombra fotos y escaneos con la fecha y un número: `2026-11-06_001.jpg`. |
| `copiar-apuntes` | `copiar` | Copia los PDF y DOCX de Apuntes a una carpeta de seguridad. |
| `borrar-temporales` | `borrar` | Borra los `.tmp` de Descargas después de pedir confirmación. |

Las rutas de `acciones.json` son un punto de partida: puedes cambiarlas sin tocar el código.
Antes de ejecutar una acción destructiva, prueba siempre con `--simular`.

## Pruebas

La batería de pruebas usa `pytest` y carpetas temporales, así que nunca toca tus ficheros reales:

```bash
uv run pytest -q
```

| Fichero | Qué comprueba |
|---|---|
| `tests/test_config.py` | Carga del JSON, versión del esquema, campos obligatorios, filtros y errores. |
| `tests/test_acciones.py` | Mover, copiar, renombrar y borrar; colisiones de nombres y `--simular`. |
| `tests/test_motor.py` | Selección por extensión, patrón, antigüedad y tamaño; ejecución de acciones. |
| `tests/test_cli.py` | Órdenes de Typer, códigos de salida, confirmación y cancelación del borrado. |

## Esquema de acciones.json

El fichero `acciones.json` describe las acciones sin tocar el código.
Este es el esquema que valida `config.py`.

### Raíz

| Campo | Obligatorio | Tipo | Descripción |
|---|---|---|---|
| `version` | Sí | entero | Versión del esquema. Actualmente debe ser `1`. |
| `acciones` | Sí | lista | Lista de acciones. No puede estar vacía. |

### Cada acción

| Campo | Obligatorio | Tipo | Descripción |
|---|---|---|---|
| `nombre` | Sí | texto | Identificador único, en minúsculas y con guiones. |
| `descripcion` | Sí | texto | Frase que explica qué hace la acción. |
| `tipo` | Sí | texto | `mover`, `copiar`, `renombrar` o `borrar`. |
| `origen` | No | ruta | Carpeta por defecto si no se pasa `CARPETA`. Admite `~`. |
| `destino` | Sí en `mover` y `copiar` | ruta | Carpeta a la que se mueve o copia. Admite `~`. |
| `plantilla` | Sí en `renombrar` | texto | Nombre nuevo con huecos. |
| `filtro` | No | objeto | Qué ficheros se tocan. |

### Filtros

| Campo | Tipo | Descripción |
|---|---|---|
| `extensiones` | lista de textos | Solo esas extensiones, por ejemplo `[".pdf", ".docx"]`. |
| `patron` | texto | Expresión regular sobre el nombre del fichero. |
| `mas_antiguo_que_dias` | entero | Solo ficheros modificados hace más de N días. |
| `mayor_que_mb` | número | Solo ficheros de más de N MB. |

### Plantillas de nombre

| Hueco | Ejemplo | Resultado |
|---|---|---|
| `{fecha:%Y-%m-%d}` | `{fecha:%Y-%m-%d}` | `2026-11-06` |
| `{n:03}` | `{n:03}` | `001`, `002`… |
| `{ext}` | `{ext}` | `.jpg` |
| `{nombre}` | `{nombre}` | Nombre original sin extensión. |

## Seguridad

- Las acciones destructivas piden confirmación salvo que se use `--si`.
- `--simular` enseña lo que se haría sin tocar el disco.
- Nunca se sobrescribe un fichero: si el destino existe, se añade ` (1)`, ` (2)`…
- Las claves y secretos van en variables de entorno o en `.env`, que está ignorado por git.
- Las pruebas se hacen en `pruebas-tareas/` y siempre con `--simular` primero.

## Estructura

```text
src/tareas/
  __init__.py      versión del paquete
  __main__.py      permite python -m tareas
  cli.py           órdenes Typer y salida Rich
  config.py        carga y valida acciones.json
  errores.py       TareasError, ConfigError y AccionNoValida
  acciones.py      clases Mover, Copiar, Renombrar y Borrar
  motor.py         selecciona ficheros y ejecuta acciones
acciones.json      mis acciones
tests/             pruebas de config, acciones, motor y CLI con pytest
docs/adr/          decisiones de arquitectura
docs/prompts.md    prompts clave del proceso
```
