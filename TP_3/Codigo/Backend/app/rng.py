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
    semilla_base: int,
    a: int,
    c: int,
    m: int,
    nombres_variables: list[str],
) -> dict[str, GeneradorCongruencialMixto]:
    """Crea el mapeo {variable: generador} SIN offsets primos.

    Ya no se desplaza la semilla por variable: se crea UN ÚNICO
    GeneradorCongruencialMixto (semilla_base, a, c, m) y se lo referencia
    desde todas las variables. Como es el mismo objeto, cada llamada a
    `.uniforme()` -sin importar desde qué variable se haga- avanza el
    MISMO stream secuencial (X0 -> X1 -> X2 -> ...), en vez de que cada
    variable tenga su propio punto de partida.

    Sigue siendo 100% reproducible: mismos (semilla_base, a, c, m) =>
    misma secuencia de números.

    Atención: al compartir un único stream, los U(0,1) que le tocan a
    cada variable dependen del ORDEN en que se los pida (por eso
    `red_proyecto.py` siempre recorre las actividades en el mismo orden
    topológico). Si dos variables piden un número "al mismo tiempo" en
    ramas paralelas, iguel se van a servir en el orden en que el código
    las procese, no en paralelo real.
    """
    generador_unico = GeneradorCongruencialMixto(
        semilla=semilla_base, a=a, c=c, m=m)

    # for nombre in nombres_variables:
    #     generador_unico.siguiente_entero()
    #     print(generador_unico.toString())
    return {nombre: generador_unico for nombre in nombres_variables}
