from pydantic import BaseModel, Field


class ConfigGCM(BaseModel):
    """Parámetros del Generador Congruencial Mixto base.

    Por defecto trae los valores de prueba del enunciado
    (semilla=3922, a=1221, c=1714). El módulo `m` es el número de legajo
    y es obligatorio, ya que cambia por alumno.
    """

    semilla: int = Field(3922, description="Semilla (X0) del generador")
    a: int = Field(1221, description="Constante multiplicativa")
    c: int = Field(1714, description="Constante aditiva")
    m: int = Field(..., gt=0, description="Módulo del generador (número de legajo)")


class SimulacionUnicaRequest(BaseModel):
    rng: ConfigGCM


class SimulacionLoteRequest(BaseModel):
    rng: ConfigGCM
    n: int = Field(..., gt=0, description="Cantidad de réplicas a simular")
    umbral_menor_igual: float = Field(60, description="Minutos para P(T <= umbral)")
    umbral_mayor_igual: float = Field(90, description="Minutos para P(T >= umbral)")


class ConfianzaRequest(BaseModel):
    rng: ConfigGCM
    n: int = Field(99, gt=1, description="Cantidad de réplicas (99 según enunciado)")
    nivel_confianza: float = Field(0.95, gt=0, lt=1)
