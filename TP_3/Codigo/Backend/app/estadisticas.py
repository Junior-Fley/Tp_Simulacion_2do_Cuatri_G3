"""
Estimadores calculados de forma ONLINE / incremental: en todo momento solo
se guarda el "vector actual" (n, media, M2, mínimo, contadores) y se
actualiza con cada nueva observación, tal como exige la consigna
("el software solo debe trabajar con el vector actual y el vector
anterior... no debe almacenar tablas de datos").

- OnlineStats: media y varianza vía el algoritmo de Welford (streaming).
- ContadorProporcion: proporción de veces que ocurre un evento (ej. que una
  rama sea crítica), sin guardar cada resultado individual.
- HistogramaOnline: clasifica cada observación en su intervalo apenas
  llega, incrementando solo un contador por bin.
"""

from __future__ import annotations

import math


class OnlineStats:
    """Media, varianza, mínimo y máximo calculados en un solo pasaje
    (algoritmo de Welford), sin guardar la lista de observaciones."""

    def __init__(self) -> None:
        self.n: int = 0
        self.media: float = 0.0
        self._m2: float = 0.0
        self.minimo: float | None = None
        self.maximo: float | None = None

    def actualizar(self, x: float) -> None:
        self.n += 1
        delta = x - self.media
        self.media += delta / self.n
        delta2 = x - self.media
        self._m2 += delta * delta2
        self.minimo = x if self.minimo is None else min(self.minimo, x)
        self.maximo = x if self.maximo is None else max(self.maximo, x)

    @property
    def varianza(self) -> float:
        return self._m2 / (self.n - 1) if self.n > 1 else 0.0

    @property
    def desvio_estandar(self) -> float:
        return math.sqrt(self.varianza)

    def como_dict(self) -> dict:
        return {
            "n": self.n,
            "media": self.media,
            "varianza": self.varianza,
            "desvio_estandar": self.desvio_estandar,
            "minimo": self.minimo,
            "maximo": self.maximo,
        }


class ContadorProporcion:
    """Cuenta ocurrencias de distintas categorías (ej. qué rama fue
    crítica en cada réplica) sin guardar el detalle de cada réplica."""

    def __init__(self) -> None:
        self.total: int = 0
        self._conteos: dict[str, int] = {}

    def actualizar(self, categoria: str) -> None:
        self.total += 1
        self._conteos[categoria] = self._conteos.get(categoria, 0) + 1

    def proporciones(self) -> dict[str, float]:
        if self.total == 0:
            return {}
        return {cat: cuenta / self.total for cat, cuenta in self._conteos.items()}


class ContadorUmbral:
    """P(X <= umbral) o P(X >= umbral), acumulado online."""

    def __init__(self, umbral: float, modo: str) -> None:
        assert modo in ("menor_igual", "mayor_igual")
        self.umbral = umbral
        self.modo = modo
        self.total = 0
        self.cumple = 0

    def actualizar(self, x: float) -> None:
        self.total += 1
        if self.modo == "menor_igual" and x <= self.umbral:
            self.cumple += 1
        elif self.modo == "mayor_igual" and x >= self.umbral:
            self.cumple += 1

    @property
    def probabilidad(self) -> float:
        return self.cumple / self.total if self.total else 0.0


class HistogramaOnline:
    """Distribución de frecuencias de 10 intervalos, construida online.

    - extremo_inferior: mínimo de tiempo calculado (límite inferior del 1er
      intervalo).
    - Los primeros 9 intervalos son de igual ancho y cubren desde
      extremo_inferior hasta extremo_inferior + 90.
    - El 10º intervalo arranca en extremo_inferior + 90 y absorbe todo el
      resto (abierto hacia arriba).
    """

    def __init__(self, extremo_inferior: float, ancho_total: float = 90.0, n_intervalos_iguales: int = 9) -> None:
        self.extremo_inferior = extremo_inferior
        self.ancho_intervalo = ancho_total / n_intervalos_iguales
        self.bordes: list[float] = [
            extremo_inferior + i * self.ancho_intervalo for i in range(n_intervalos_iguales + 1)
        ]  # 10 bordes -> 9 intervalos cerrados + el último se reabre abajo
        self.conteos: list[int] = [0] * (n_intervalos_iguales + 1)  # 9 + 1 (cola)
        self.n = 0

    def actualizar(self, x: float) -> None:
        self.n += 1
        # Intervalos [borde_i, borde_(i+1)) para los primeros 9
        for i in range(len(self.bordes) - 1):
            if self.bordes[i] <= x < self.bordes[i + 1]:
                self.conteos[i] += 1
                return
        # Todo lo que no cayó en los primeros 9 va al intervalo final (cola)
        self.conteos[-1] += 1

    def como_lista(self) -> list[dict]:
        intervalos = []
        for i in range(len(self.bordes) - 1):
            intervalos.append(
                {
                    "intervalo": i + 1,
                    "desde": round(self.bordes[i], 4),
                    "hasta": round(self.bordes[i + 1], 4),
                    "frecuencia": self.conteos[i],
                    "frecuencia_relativa": self.conteos[i] / self.n if self.n else 0.0,
                }
            )
        intervalos.append(
            {
                "intervalo": len(self.bordes),
                "desde": round(self.bordes[-1], 4),
                "hasta": None,  # abierto
                "frecuencia": self.conteos[-1],
                "frecuencia_relativa": self.conteos[-1] / self.n if self.n else 0.0,
            }
        )
        return intervalos


def z_para_confianza(confianza: float, una_cola: bool = True) -> float:
    """Valor z de la normal estándar para el nivel de confianza pedido.

    Usa la aproximación racional de Acklam (sin dependencias externas como
    scipy) para el cuantil de la normal estándar inversa.
    """
    p = confianza if una_cola else 1 - (1 - confianza) / 2
    return _norm_ppf(p)


def _norm_ppf(p: float) -> float:
    """Aproximación de Peter Acklam para la inversa de la normal estándar."""
    if not (0 < p < 1):
        raise ValueError("p debe estar entre 0 y 1")

    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]

    p_low = 0.02425
    p_high = 1 - p_low

    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
