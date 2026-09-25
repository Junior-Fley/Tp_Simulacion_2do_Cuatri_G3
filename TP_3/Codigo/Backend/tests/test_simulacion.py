"""Tests básicos de reproducibilidad y consistencia del modelo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rng import GeneradorCongruencialMixto, crear_generadores_por_variable
from app.schemas import ConfigGCM
from app.red_proyecto import NOMBRES_VARIABLES_ALEATORIAS, simular_una_replica
from app.simulador import calcular_tiempo_con_confianza, simular_lote, simular_replica_unica


def test_generador_es_determinístico():
    g1 = GeneradorCongruencialMixto(semilla=3922, a=1221, c=1714, m=12347)
    g2 = GeneradorCongruencialMixto(semilla=3922, a=1221, c=1714, m=12347)
    secuencia1 = [g1.uniforme() for _ in range(20)]
    secuencia2 = [g2.uniforme() for _ in range(20)]
    assert secuencia1 == secuencia2


def test_generador_no_guarda_historial():
    g = GeneradorCongruencialMixto(semilla=3922, a=1221, c=1714, m=12347)
    for _ in range(50):
        g.uniforme()
    estado = g.estado()
    assert set(estado.keys()) == {"x_actual", "x_anterior", "llamadas_realizadas"}


def test_replica_respeta_precedencias():
    generadores = crear_generadores_por_variable(3922, 1221, 1714, 45123, NOMBRES_VARIABLES_ALEATORIAS)
    resultado = simular_una_replica(generadores)
    finalizacion = resultado["tiempos_finalizacion"]
    assert finalizacion["B"] >= finalizacion["A"]
    assert finalizacion["D"] >= finalizacion["C"]
    assert finalizacion["E"] >= finalizacion["D"]
    assert finalizacion["F"] >= finalizacion["B"]
    assert finalizacion["F"] >= finalizacion["E"]
    assert resultado["duracion_total_proyecto"] == finalizacion["Fin"] == finalizacion["F"]


def test_lote_es_reproducible():
    cfg = ConfigGCM(semilla=3922, a=1221, c=1714, m=45123)
    lote1 = simular_lote(cfg, n=150, umbral_menor_igual=60, umbral_mayor_igual=90)
    lote2 = simular_lote(cfg, n=150, umbral_menor_igual=60, umbral_mayor_igual=90)
    assert lote1["duracion_proyecto"] == lote2["duracion_proyecto"]
    assert lote1["distribucion_de_frecuencias"] == lote2["distribucion_de_frecuencias"]


def test_lote_suma_de_frecuencias_es_n():
    cfg = ConfigGCM(semilla=3922, a=1221, c=1714, m=45123)
    n = 300
    lote = simular_lote(cfg, n=n, umbral_menor_igual=60, umbral_mayor_igual=90)
    total = sum(intervalo["frecuencia"] for intervalo in lote["distribucion_de_frecuencias"])
    assert total == n


def test_proyecto_nunca_es_mas_corto_que_60():
    # Con los parámetros del enunciado (A=15, discreta B, etc.) el mínimo
    # teórico de la rama Producto es 15+20+15=50, por lo que ninguna
    # réplica puede durar menos de 50 minutos.
    cfg = ConfigGCM(semilla=3922, a=1221, c=1714, m=45123)
    resultado = simular_replica_unica(cfg)
    assert resultado["duracion_total_proyecto"] >= 50


def test_confianza_devuelve_tiempo_mayor_a_la_media():
    cfg = ConfigGCM(semilla=3922, a=1221, c=1714, m=45123)
    resultado = calcular_tiempo_con_confianza(cfg, n=99, nivel_confianza=0.95)
    assert resultado["tiempo_a_fijar_minutos"] > resultado["media_muestral"]
