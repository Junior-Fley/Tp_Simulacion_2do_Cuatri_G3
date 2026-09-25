"""
Modelo de la red de actividades del pedido online (diagrama con actividades
en paralelo) y lógica para simular UNA réplica del proceso completo.

Estructura del proyecto:

    Inicio -> A -> B ----\
                            -> F -> Fin
    Inicio -> C -> D -> E -/

F solo puede comenzar cuando B **y** E hayan finalizado.
"""

from __future__ import annotations

from distribuciones import (
    muestrear_constante,
    muestrear_discreta,
    muestrear_exponencial,
    muestrear_uniforme,
)
from rng import GeneradorCongruencialMixto

# Orden topológico: cada actividad se procesa después que sus predecesoras.
ORDEN_TOPOLOGICO: list[str] = ["Inicio", "A", "C", "B", "D", "E", "F", "Fin"]

# Definición de cada actividad: tipo de distribución, parámetros y
# predecesoras (según "Preparación de caso para Simulación" del enunciado).
DEFINICION_ACTIVIDADES: dict[str, dict] = {
    "Inicio": {
        "descripcion": "Pedido Recibido / Confirmación de Pedido en Web",
        "tipo": "constante",
        "valor": 0,
        "predecesoras": [],
    },
    "A": {
        "descripcion": "Verificación de Pago y Stock",
        "tipo": "constante",
        "valor": 15,
        "predecesoras": ["Inicio"],
    },
    "B": {
        "descripcion": "Picking en Almacén",
        "tipo": "discreta",
        "valores": [20, 30, 40],
        "probabilidades": [0.25, 0.40, 0.35],
        "predecesoras": ["A"],
    },
    "C": {
        "descripcion": "Impresión de Etiqueta y Factura",
        "tipo": "constante",
        "valor": 5,
        "predecesoras": ["Inicio"],
    },
    "D": {
        "descripcion": "Preparación de Empaque (Packing)",
        "tipo": "uniforme",
        "minimo": 5,
        "maximo": 25,
        "predecesoras": ["C"],
    },
    "E": {
        "descripcion": "Control de Calidad y Pesaje",
        "tipo": "exponencial",
        "media": 5,
        "predecesoras": ["D"],
    },
    "F": {
        "descripcion": "Despacho y Carga al Camión",
        "tipo": "discreta",
        "valores": [15, 25],
        "probabilidades": [0.50, 0.50],
        "predecesoras": ["B", "E"],
    },
    "Fin": {
        "descripcion": "Pedido Despachado",
        "tipo": "constante",
        "valor": 0,
        "predecesoras": ["F"],
    },
}

NOMBRES_VARIABLES_ALEATORIAS = list(DEFINICION_ACTIVIDADES.keys())


def _muestrear_actividad(definicion: dict, u: float | None) -> float:
    tipo = definicion["tipo"]
    if tipo == "constante":
        return muestrear_constante(definicion["valor"])
    if tipo == "discreta":
        return muestrear_discreta(definicion["valores"], definicion["probabilidades"], u)
    if tipo == "uniforme":
        return muestrear_uniforme(definicion["minimo"], definicion["maximo"], u)
    if tipo == "exponencial":
        return muestrear_exponencial(definicion["media"], u)
    raise ValueError(f"Tipo de distribución desconocido: {tipo}")


def simular_una_replica(
    generadores: dict[str, GeneradorCongruencialMixto],
) -> dict:
    """Ejecuta UNA réplica completa del proceso logístico.

    Usa un generador (stream) distinto por variable, y solo trabaja con el
    valor actual devuelto por cada uno: no arma tablas ni historiales.
    """
    duraciones: dict[str, float] = {}
    finalizacion: dict[str, float] = {}

    for nombre in ORDEN_TOPOLOGICO:
        definicion = DEFINICION_ACTIVIDADES[nombre]
        generador = generadores[nombre]
        u = None if definicion["tipo"] == "constante" else generador.uniforme()
        duracion = _muestrear_actividad(definicion, u)

        predecesoras = definicion["predecesoras"]
        inicio_actividad = max((finalizacion[p]
                               for p in predecesoras), default=0.0)

        duraciones[nombre] = duracion
        finalizacion[nombre] = inicio_actividad + duracion

    tiempo_ruta_producto = finalizacion["B"]  # rama Inicio->A->B
    tiempo_ruta_empaque = finalizacion["E"]  # rama Inicio->C->D->E

    # La rama que llega más tarde a F es la que determina cuándo arranca F:
    # esa es la rama "crítica" de esta réplica.
    if tiempo_ruta_producto >= tiempo_ruta_empaque:
        ruta_critica = "Producto (A-B)"
    else:
        ruta_critica = "Empaque (C-D-E)"

    return {
        "duraciones": duraciones,
        "tiempos_finalizacion": finalizacion,
        "tiempo_ruta_producto": tiempo_ruta_producto,
        "tiempo_ruta_empaque": tiempo_ruta_empaque,
        "ruta_critica": ruta_critica,
        "duracion_total_proyecto": finalizacion["Fin"],
    }
