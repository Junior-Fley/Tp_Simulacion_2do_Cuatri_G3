"""
Orquesta las simulaciones combinando rng + red_proyecto + estadisticas.

Todo se calcula de forma incremental (online): para un lote de n réplicas
nunca se arma una lista con las n duraciones; cada resultado se usa para
actualizar los acumuladores (OnlineStats, ContadorProporcion, etc.) y se
descarta.

Para el histograma se necesita conocer primero el tiempo mínimo, por lo
que se hacen DOS pasadas de simulación. Como el generador es determinístico
(misma semilla => misma secuencia), la segunda pasada reproduce
exactamente las mismas n réplicas que la primera, sin necesidad de haber
guardado ningún dato de la primera pasada.
"""

from __future__ import annotations

from estadisticas import ContadorProporcion, ContadorUmbral, HistogramaOnline, OnlineStats, z_para_confianza
from red_proyecto import DEFINICION_ACTIVIDADES, NOMBRES_VARIABLES_ALEATORIAS, simular_una_replica
from rng import crear_generadores_por_variable
from schemas import ConfigGCM


def _nuevos_generadores(config: ConfigGCM):
    return crear_generadores_por_variable(
        semilla_base=config.semilla,
        a=config.a,
        c=config.c,
        m=config.m,
        nombres_variables=NOMBRES_VARIABLES_ALEATORIAS,
    )


def simular_replica_unica(config: ConfigGCM) -> dict:
    generadores = _nuevos_generadores(config)
    return simular_una_replica(generadores)


def simular_lote(config: ConfigGCM, n: int, umbral_menor_igual: float, umbral_mayor_igual: float) -> dict:
    """Corre n réplicas y calcula todos los estimadores pedidos en el TP,
    trabajando siempre de forma online (sin tablas)."""

    # --- Pasada 1: estimadores que se pueden calcular en un solo pasaje ---
    generadores = _nuevos_generadores(config)

    stats_proyecto = OnlineStats()
    stats_por_actividad = {nombre: OnlineStats()
                           for nombre in DEFINICION_ACTIVIDADES}
    contador_ruta_critica = ContadorProporcion()
    contador_menor_igual = ContadorUmbral(umbral_menor_igual, "menor_igual")
    contador_mayor_igual = ContadorUmbral(umbral_mayor_igual, "mayor_igual")

    # promedio móvil hasta cada iteración (pedido explícitamente)
    medias_acumuladas: list[float] = []

    for _ in range(n):
        resultado = simular_una_replica(generadores)

        stats_proyecto.actualizar(resultado["duracion_total_proyecto"])
        for nombre, duracion in resultado["duraciones"].items():
            stats_por_actividad[nombre].actualizar(duracion)

        contador_ruta_critica.actualizar(resultado["ruta_critica"])
        contador_menor_igual.actualizar(resultado["duracion_total_proyecto"])
        contador_mayor_igual.actualizar(resultado["duracion_total_proyecto"])

        medias_acumuladas.append(stats_proyecto.media)

    tiempo_minimo_estimado = stats_proyecto.minimo

    # --- Pasada 2: histograma de 10 intervalos, ahora que ya sabemos el mínimo ---
    # Se reinician los MISMOS generadores (misma semilla) => se reproducen
    # exactamente las mismas n réplicas, sin haber guardado ningún dato.
    generadores_pasada_2 = _nuevos_generadores(config)
    histograma = HistogramaOnline(
        extremo_inferior=tiempo_minimo_estimado, ancho_total=90.0, n_intervalos_iguales=9)
    for _ in range(n):
        resultado = simular_una_replica(generadores_pasada_2)
        histograma.actualizar(resultado["duracion_total_proyecto"])

    return {
        "n_replicas": n,
        "duracion_proyecto": stats_proyecto.como_dict(),
        "tiempo_minimo_estimado_proyecto": tiempo_minimo_estimado,
        "duracion_promedio_por_actividad": {
            nombre: stats.como_dict() for nombre, stats in stats_por_actividad.items()
        },
        "promedio_movil_duracion_proyecto": medias_acumuladas,
        "proporcion_ruta_critica": contador_ruta_critica.proporciones(),
        "probabilidad_terminar_en_o_antes_de": {
            "umbral_minutos": umbral_menor_igual,
            "probabilidad": contador_menor_igual.probabilidad,
        },
        "probabilidad_terminar_en_o_despues_de": {
            "umbral_minutos": umbral_mayor_igual,
            "probabilidad": contador_mayor_igual.probabilidad,
        },
        "distribucion_de_frecuencias": histograma.como_lista(),
    }


def calcular_tiempo_con_confianza(config: ConfigGCM, n: int, nivel_confianza: float) -> dict:
    """Simula n réplicas (por defecto 99, según el enunciado) y calcula el
    tiempo T tal que P(finalizar en <= T) sea al menos `nivel_confianza`,
    usando el límite superior de confianza unilateral para la media:

        T = media + z_(confianza) * (desvio_estandar / sqrt(n))
    """
    generadores = _nuevos_generadores(config)
    stats_proyecto = OnlineStats()
    for _ in range(n):
        resultado = simular_una_replica(generadores)
        stats_proyecto.actualizar(resultado["duracion_total_proyecto"])

    z = z_para_confianza(nivel_confianza, una_cola=True)
    error_estandar = stats_proyecto.desvio_estandar / (n ** 0.5)
    tiempo_a_fijar = stats_proyecto.media + z * error_estandar

    return {
        "n_replicas": n,
        "nivel_confianza": nivel_confianza,
        "media_muestral": stats_proyecto.media,
        "desvio_estandar_muestral": stats_proyecto.desvio_estandar,
        "z": z,
        "error_estandar": error_estandar,
        "tiempo_a_fijar_minutos": tiempo_a_fijar,
        "interpretacion": (
            f"Con {int(nivel_confianza * 100)}% de confianza, el proyecto puede "
            f"completarse en {tiempo_a_fijar:.2f} minutos o menos."
        ),
    }
