# Simulación de Proyecto Logístico (sin memoria) — Backend FastAPI

Backend que resuelve el TP "Análisis de Proyecto logístico sin memoria": modela
el despacho de un pedido online como una red de actividades con dos ramas en
paralelo (Producto y Empaque) que convergen en la actividad **F**, y simula el
proceso usando un **Generador Congruencial Mixto (GCM) individual por
variable aleatoria**, calculando todos los estimadores pedidos **sin
almacenar tablas de datos** (solo vector actual/anterior).

## Red de actividades modelada

```
Inicio -> A (15 min, cte) -> B (discreta: 20/30/40) ----\
                                                            -> F -> Fin
Inicio -> C (5 min, cte) -> D (uniforme 5-25) -> E (exponencial, media 5) -/
```

F (discreta: 15/25 min, según disponibilidad de montacargas) solo puede
empezar cuando **B y E** ya terminaron.

## Estructura del proyecto

```
app/
  rng.py             -> Generador Congruencial Mixto (uno por variable, sin historial)
  distribuciones.py  -> Muestreo por transformada inversa (constante, discreta, uniforme, exponencial)
  red_proyecto.py     -> Definición de la red + lógica de UNA réplica
  estadisticas.py     -> Estimadores ONLINE: media/varianza (Welford), proporciones,
                          probabilidades por umbral, histograma de 10 intervalos, z de confianza
  simulador.py         -> Orquesta réplica única / lote / cálculo de confianza 95%
  schemas.py           -> Modelos Pydantic de entrada
  main.py              -> Endpoints FastAPI
tests/
  test_simulacion.py   -> Tests de reproducibilidad y consistencia (pytest)
requirements.txt
```

## Cómo se garantiza que sea "sin memoria"

- `GeneradorCongruencialMixto` solo guarda `x_actual` y `x_anterior` (nada de listas).
- Los estimadores de `estadisticas.py` se actualizan de a una observación por vez
  (algoritmo de **Welford** para media/varianza, contadores simples para
  proporciones y probabilidades, y el histograma clasifica cada dato apenas
  llega). En ningún momento se arma una lista con las *n* duraciones simuladas.
- El histograma necesita conocer el mínimo del proyecto antes de fijar los
  intervalos. Como el generador es **determinístico** (misma semilla ⇒ misma
  secuencia), se hace una **segunda pasada** que reproduce exactamente las
  mismas *n* réplicas para clasificarlas en los intervalos, sin necesidad de
  haber guardado ningún dato de la primera pasada.

## Instalación y ejecución

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Documentación interactiva (Swagger): http://127.0.0.1:8000/docs

## Endpoints

### `GET /actividades`
Devuelve la definición completa de la red (actividades, predecesoras,
distribuciones).

### `POST /simular/replica-unica`
Corre **una** réplica y devuelve la duración de cada actividad, los tiempos
de finalización y qué rama resultó crítica.

```json
{
  "rng": { "semilla": 3922, "a": 1221, "c": 1714, "m": 45123 }
}
```

> `m` es el **módulo del generador = número de legajo** (obligatorio, distinto
> por alumno según el enunciado). `semilla`, `a` y `c` ya vienen precargados
> con los valores de prueba (3922, 1221, 1714) pero se pueden pisar con los
> que se den al momento de evaluar.

### `POST /simular/lote`
Corre *n* réplicas y devuelve, todo calculado en línea (sin tablas):

- Duración del proyecto: media, varianza, desvío, mínimo y máximo.
- **Tiempo mínimo estimado del proyecto** (vía simulación, no teórico).
- Duración promedio de **cada actividad**.
- **Promedio móvil** de la duración del proyecto hasta cada iteración.
- **Proporción de veces que cada rama fue crítica** (cuello de botella).
- `P(finalizar en <= umbral_menor_igual)` — por defecto 60 minutos.
- `P(finalizar en >= umbral_mayor_igual)` — por defecto 90 minutos.
- **Distribución de frecuencias en 10 intervalos** (9 de igual ancho desde el
  mínimo simulado, cubriendo 90 minutos, + 1 intervalo final que absorbe el
  resto).

```json
{
  "rng": { "semilla": 3922, "a": 1221, "c": 1714, "m": 45123 },
  "n": 1000,
  "umbral_menor_igual": 60,
  "umbral_mayor_igual": 90
}
```

### `POST /simular/tiempo-con-confianza`
Simula *n* veces (**99 por defecto**, tal como pide el enunciado) y calcula el
tiempo a fijar para completar el proyecto con el nivel de confianza pedido
(**95% por defecto**), usando el límite superior de confianza unilateral para
la media:

```
T = media + z(confianza) * (desvío_estándar / sqrt(n))
```

```json
{
  "rng": { "semilla": 3922, "a": 1221, "c": 1714, "m": 45123 },
  "n": 99,
  "nivel_confianza": 0.95
}
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```

Verifican: reproducibilidad del generador, que no se guarda historial, que se
respetan las precedencias de la red, que el lote es reproducible, que el
histograma suma exactamente *n*, y que el tiempo con confianza es siempre
mayor a la media muestral.

## Notas sobre el cumplimiento de la consigna

- **Generador individual por variable**: `crear_generadores_por_variable`
  crea un `GeneradorCongruencialMixto` distinto para cada actividad
  (Inicio, A, B, C, D, E, F, Fin), desplazando la semilla base con offsets
  primos fijos, para que las variables no queden correlacionadas entre sí,
  manteniendo total reproducibilidad.
- **Módulo = legajo**: se pasa como parámetro `m` en cada request; no está
  hardcodeado, para que cada integrante del grupo lo use con su propio
  número al momento de la evaluación individual.
- **Distribuciones**: constante, discreta (transformada inversa con
  acumulada), uniforme y exponencial, tal como se pide en la tabla
  "Preparación de caso para Simulación".
- **Ruta crítica / cuello de botella**: en cada réplica se compara el tiempo
  de la rama Producto (`A→B`) contra la rama Empaque (`C→D→E`); la que llega
  más tarde a F es la que se cuenta como crítica en esa réplica.
