"""
Backend FastAPI para el TP de "Análisis de Proyecto logístico sin memoria".

Ejecutar con:
    uvicorn app.main:app --reload

Documentación interactiva en: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from red_proyecto import DEFINICION_ACTIVIDADES, ORDEN_TOPOLOGICO
from schemas import ConfianzaRequest, SimulacionLoteRequest, SimulacionUnicaRequest
from simulador import calcular_tiempo_con_confianza, simular_lote, simular_replica_unica

app = FastAPI(
    title="Simulación de Proyecto Logístico (sin memoria)",
    description=(
        "API para simular el proceso de despacho de un pedido online modelado "
        "como una red de actividades con dos ramas en paralelo (Producto y "
        "Empaque) que convergen en la actividad F. Usa un Generador "
        "Congruencial Mixto individual por variable aleatoria y calcula todos "
        "los estimadores trabajando siempre con el vector actual/anterior, "
        "sin almacenar tablas de datos."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def raiz():
    return {
        "mensaje": "API de simulación de proyecto logístico. Ver /docs para la documentación interactiva.",
    }


@app.get("/actividades", tags=["Red de actividades"])
def obtener_red_de_actividades():
    """Devuelve la definición completa de la red: actividades, predecesoras
    y distribución de probabilidad de cada una."""
    return {
        "orden_topologico": ORDEN_TOPOLOGICO,
        "actividades": DEFINICION_ACTIVIDADES,
        "logica": {
            "rama_producto": ["Inicio", "A", "B"],
            "rama_empaque": ["Inicio", "C", "D", "E"],
            "convergencia": "F requiere que B y E estén ambas finalizadas",
            "cierre": ["F", "Fin"],
        },
    }


@app.post("/simular/replica-unica", tags=["Simulación"])
def endpoint_replica_unica(request: SimulacionUnicaRequest):
    """Corre UNA sola réplica del proceso y devuelve el detalle
    (duración de cada actividad, tiempos de finalización y ruta crítica)."""
    try:
        return simular_replica_unica(request.rng)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/simular/lote", tags=["Simulación"])
def endpoint_simular_lote(request: SimulacionLoteRequest):
    """Corre n réplicas y devuelve, todo calculado de forma online:

    - Duración estimada del proyecto (media, varianza, mínimo, máximo).
    - Tiempo mínimo del proyecto obtenido en la simulación.
    - Duración promedio de cada actividad.
    - Promedio móvil de la duración del proyecto hasta cada iteración.
    - Proporción de veces que cada rama (Producto / Empaque) fue crítica
      (cuello de botella).
    - P(finalizar en <= umbral_menor_igual minutos).
    - P(finalizar en >= umbral_mayor_igual minutos).
    - Distribución de frecuencias en 10 intervalos (9 iguales + 1 cola),
      arrancando en el tiempo mínimo estimado.
    """
    try:
        return simular_lote(
            config=request.rng,
            n=request.n,
            umbral_menor_igual=request.umbral_menor_igual,
            umbral_mayor_igual=request.umbral_mayor_igual,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/simular/tiempo-con-confianza", tags=["Simulación"])
def endpoint_tiempo_con_confianza(request: ConfianzaRequest):
    """Simulando n veces (99 por defecto, según el enunciado), calcula el
    tiempo a fijar para completar el proyecto con el nivel de confianza
    pedido (95% por defecto)."""
    try:
        return calcular_tiempo_con_confianza(
            config=request.rng,
            n=request.n,
            nivel_confianza=request.nivel_confianza,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
