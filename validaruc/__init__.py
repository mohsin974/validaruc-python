"""validaruc — cliente Python mínimo para ValidaRUC.

Validación de RUC peruano sobre el Padrón Reducido de la SUNAT
(dataset público, actualizado a diario).

    from validaruc import ValidaRUC

    api = ValidaRUC(api_key="TU_RAPIDAPI_KEY")
    api.checksum("10452159428")   # True — offline, sin red
    r = api.consultar("10452159428")
    print(r.razon_social, r.estado, r.condicion)
"""

from .client import ValidaRUC, RucData, checksum_ruc
from .exceptions import (
    ValidaRUCError,
    RucInvalido,
    RucNoEncontrado,
    CuotaSuperada,
)

__all__ = [
    "ValidaRUC",
    "RucData",
    "checksum_ruc",
    "ValidaRUCError",
    "RucInvalido",
    "RucNoEncontrado",
    "CuotaSuperada",
]

__version__ = "0.1.0"
