# ADR-0002: La IA explica acciones, pero no las ejecuta

- Estado: aceptada
- Fecha: 2026-11-06
- Autor: Borja Herreros

## Contexto

La práctica pide una funcionalidad de IA. Mi herramienta mueve, copia, renombra y
borra ficheros; si un modelo decidiera qué ficheros tocar, un error podría destruir
datos. Además, la clave de Gemini no puede acabar en el repositorio y no quiero
añadir una dependencia grande para una sola llamada.

## Decisión

Añado `tareas explicar NOMBRE [CARPETA]`, una orden de solo lectura que pide a Gemini
una explicación de lo que haría una acción. El motor selecciona los ficheros con el
mismo código que `ejecutar` y simula la acción (`simular=True`) para calcular los
nombres de destino finales, pero `explicar` no llama a ninguna operación de escritura.

La petición se construye en `ia.py` y solo contiene la configuración de la acción
(incluidas las rutas configuradas) y los nombres de los ficheros seleccionados.
Nunca se envían los contenidos de los ficheros.

La IA está detrás de un `Protocol` (`ProveedorIA`) con una implementación `Gemini`
que usa `urllib` de la biblioteca estándar y la Interactions API. La clave se lee de
`GEMINI_API_KEY`; el modelo se puede cambiar con `GEMINI_MODELO`. En las pruebas se
inyecta un proveedor falso para no gastar cuota.

## Alternativas consideradas

1. **Que la IA decida qué ficheros mover o borrar.**
   - A favor: sería más «inteligente» y permitiría filtros en lenguaje natural.
   - En contra: un error del modelo puede perder datos; no es auditable ni
     reproducible. La práctica pide automatizar tareas concretas y seguras.

2. **Usar el SDK `google-genai`.**
   - A favor: menos código HTTP y más comodidad.
   - En contra: añade una dependencia y otra forma de instalar el proyecto. Para una
     petición de texto, `urllib` es suficiente y funciona en Linux, Windows y macOS.

3. **Usar un modelo local (por ejemplo, Ollama).**
   - A favor: no depende de Internet ni de una clave.
   - En contra: exige instalar y mantener otro programa y un modelo grande; en el
     portátil de clase no es viable.

4. **Llamar a `generateContent`.**
   - A favor: es el ejemplo clásico y hay muchos tutoriales.
   - En contra: Google recomienda la Interactions API para proyectos nuevos; los
     modelos 3 con `generateContent` pueden devolver solo pensamientos o quedarse
     sin tokens.

## Consecuencias

- **Positivas:** la orden es segura por diseño; la IA no puede borrar ni mover nada;
  la clave queda fuera del repositorio; el proveedor se puede sustituir sin tocar la
  CLI; las pruebas no gastan cuota.
- **Negativas:** depende de Internet y de la cuota de Gemini; la explicación puede
  tardar varios segundos; el modelo por defecto es un alias que Google puede
  actualizar; la calidad del texto no es determinista.
- **Qué haré si Gemini cambia:** el modelo se cambia con `GEMINI_MODELO` sin
  recompilar. Si la Interactions API cambia, solo hay que tocar `Gemini._enviar` y
  `Gemini._leer_texto`; el resto de la herramienta no se entera.
