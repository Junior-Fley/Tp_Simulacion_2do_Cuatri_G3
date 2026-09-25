"""
Muestreo de las distribuciones usadas en el TP, todas a partir de un único
U(0,1) provisto por el generador congruencial mixto de esa variable
(método de la transformada inversa).
"""

import math


def muestrear_constante(valor: float) -> float:
    """Distribución determinística: siempre devuelve el mismo valor."""
    return valor


def muestrear_discreta(valores: list[float], probabilidades: list[float], u: float) -> float:
    """Transformada inversa para una variable discreta.

    Se arma la acumulada de probabilidades y se busca el primer valor
    cuya acumulada supere a U.
    """
    acumulada = 0.0
    for valor, p in zip(valores, probabilidades):
        acumulada += p
        if u <= acumulada:
            return valor
    return valores[-1]  # resguardo por redondeo flotante


def muestrear_uniforme(minimo: float, maximo: float, u: float) -> float:
    """U[minimo, maximo] = minimo + (maximo - minimo) * U."""
    return minimo + (maximo - minimo) * u


def muestrear_exponencial(media: float, u: float) -> float:
    """Exponencial de media dada, por transformada inversa: -media * ln(1-U)."""
    u_ajustado = min(u, 1 - 1e-12)  # evita ln(0)
    return -media * math.log(1 - u_ajustado)
