# ADR-0001: Las acciones viven en acciones.json, no en el código

- Estado: aceptada
- Fecha: 2026-11-06
- Autor: Borja Herreros

## Contexto

Mi herramienta «tareas» automatiza tareas repetitivas con ficheros: mover entregas
de Descargas, renombrar escaneos de apuntes y copiar los apuntes a una carpeta de
seguridad. Son tareas que hago yo solo, varias veces por semana, y quiero poder
cambiar el filtro o la carpeta de destino sin tocar Python ni reinstalar la herramienta.

Mis primeras tres acciones son `mover-entregas`, `renombrar-escaneos` y
`copiar-apuntes`. Más adelante quiero añadir acciones de IA para resumir apuntes y
explicar conceptos, y no quiero que cada acción nueva obligue a modificar el motor.

## Decisión

Las acciones se describen en un fichero JSON externo (`acciones.json`) con un
esquema documentado en el README. El código solo contiene el motor que lee, valida
y ejecuta ese fichero. Añadir una acción significa editar el JSON, no el código.

## Alternativas consideradas

1. **Escribir cada acción como una función en Python.**
   - A favor: es lo primero que se aprende y no hace falta inventar un esquema.
   - En contra: cada cambio exige tocar el código, probarlo y reinstalar; quien no
     programa no puede añadir acciones.

2. **Usar YAML o TOML en vez de JSON.**
   - A favor: YAML es más cómodo para textos largos y TOML se lee bien.
   - En contra: JSON ya viene en la biblioteca estándar, no añade dependencias y
     Typer/Rich ya están en el proyecto.

3. **Guardar las acciones en una base de datos SQLite.**
   - A favor: permitiría historial y consultas.
   - En contra: es demasiado para tres acciones, no se puede revisar en un diff y
     complica el trabajo en clase.

## Consecuencias

- **Positivas:** añadir una acción no toca el código; el JSON se valida antes de
  ejecutar nada; los errores dicen qué acción y qué campo fallan; el fichero se puede
  revisar y versionar con git.
- **Negativas:** hay que mantener `config.py` al día cuando el esquema crezca; un
  error de escritura en el JSON solo se detecta al ejecutar `tareas validar`; el
  motor tiene que cubrir todos los tipos que se declaren.
- **Qué haré si el esquema cambia:** subiré `version` a 2, documentaré la migración
  en el README y mantendré la lectura de la versión 1 mientras tenga acciones antiguas.
