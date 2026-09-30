"""
Generador Congruencial Mixto (GCM) - "sin memoria".

Cada generador solo conserva el valor ACTUAL (X_n) y, opcionalmente, el
ANTERIOR (X_{n-1}). No se guarda ninguna tabla histórica de valores, tal
como exige la consigna.

Fórmula:
    X_(n+1) = (a * X_n + c) mod m
    U_(n+1) = X_(n+1) / m        (número pseudoaleatorio U(0,1))

Cada variable aleatoria del proyecto (A, B, C, D, E, F, ...) recibe su
PROPIO generador (su propio flujo / stream), sembrado a partir de la
semilla base pero desplazado de forma determinística. Esto evita que las
variables queden correlacionadas entre sí, y sigue siendo 100%
reproducible (mismos parámetros => misma secuencia).
"""

from dataclasses import dataclass


@dataclass
class GeneradorCongruencialMixto:
    """Generador Congruencial Mixto individual.

    Solo mantiene X_actual y X_anterior en memoria (nada de listas/tablas).
    """

    semilla: int
    a: int  # constante multiplicativa
    c: int  # constante aditiva
    m: int  # módulo (en el caso del TP: el número de legajo)

    def __post_init__(self) -> None:
        if self.m <= 0:
            raise ValueError("El módulo (m) debe ser un entero positivo.")
        self.x_actual: int = self.semilla % self.m
        self.x_anterior: int | None = None
        self._llamadas: int = 0

    def siguiente_entero(self) -> int:
        """Avanza el generador un paso y devuelve X_(n+1) (entero)."""
        self.x_anterior = self.x_actual
        self.x_actual = (self.a * self.x_actual + self.c) % self.m
        self._llamadas += 1
        return self.x_actual

    def uniforme(self) -> float:
        """Devuelve un U(0,1) a partir del siguiente entero generado."""
        x = self.siguiente_entero()
        return x / self.m

    def reiniciar(self) -> None:
        """Vuelve el generador a su estado inicial (misma semilla)."""
        self.x_actual = self.semilla % self.m
        self.x_anterior = None
        self._llamadas = 0

    def estado(self) -> dict:
        """Expone únicamente el estado actual/anterior (sin historial)."""
        return {
            "x_actual": self.x_actual,
            "x_anterior": self.x_anterior,
            "llamadas_realizadas": self._llamadas,
        }

    def toString(self) -> str:
        return str(self.x_actual)


def crear_generadores_por_variable(
    coeficientes_por_variable: dict[str, dict],
) -> dict[str, GeneradorCongruencialMixto]:
    """Crea un GeneradorCongruencialMixto INDEPENDIENTE por variable,
    usando los coeficientes que se proveen para cada una. No se derivan
    de una semilla base ni se comparten entre variables: cada variable
    aleatoria del proyecto (B, D, E, F) trae sus propios (semilla, a, c, m).

    coeficientes_por_variable = {
        "B": {"semilla": .., "a": .., "c": .., "m": ..},
        "D": {"semilla": .., "a": .., "c": .., "m": ..},
        "E": {"semilla": .., "a": .., "c": .., "m": ..},
        "F": {"semilla": .., "a": .., "c": .., "m": ..},
    }

    Sigue siendo 100% reproducible: mismos coeficientes para una variable
    => misma secuencia de números para esa variable.
    """
    return {
        nombre: GeneradorCongruencialMixto(**coefs)
        for nombre, coefs in coeficientes_por_variable.items()
    }
