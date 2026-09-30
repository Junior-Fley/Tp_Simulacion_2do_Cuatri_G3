from pydantic import BaseModel, Field


class CoeficientesGCM(BaseModel):
    semilla: int = Field(..., description="Semilla (X0) de esta variable")
    a: int = Field(..., description="Constante multiplicativa")
    c: int = Field(..., description="Constante aditiva")
    m: int = Field(..., gt=0, description="Módulo de esta variable")


class ConfigGCMPorVariable(BaseModel):
    """Coeficientes individuales para cada variable aleatoria del proyecto.
    Solo las no-constantes necesitan generador: B, D, E, F."""
    B: CoeficientesGCM
    D: CoeficientesGCM
    E: CoeficientesGCM
    F: CoeficientesGCM


class SimulacionUnicaRequest(BaseModel):
    rng: ConfigGCMPorVariable


class SimulacionLoteRequest(BaseModel):
    rng: ConfigGCMPorVariable
    n: int = Field(..., gt=0, description="Cantidad de réplicas a simular")
    umbral_menor_igual: float = Field(
        60, description="Minutos para P(T <= umbral)")
    umbral_mayor_igual: float = Field(
        90, description="Minutos para P(T >= umbral)")


class ConfianzaRequest(BaseModel):
    rng: ConfigGCMPorVariable
    n: int = Field(
        99, gt=1, description="Cantidad de réplicas (99 según enunciado)")
    nivel_confianza: float = Field(0.95, gt=0, lt=1)
