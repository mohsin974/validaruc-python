"""Cliente ValidaRUC — wrapper mínimo sobre la API REST."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests

from .exceptions import CuotaSuperada, RucInvalido, RucNoEncontrado, ValidaRUCError

RAPIDAPI_HOST = "validaruc.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

# Factores del dígito verificador (módulo 11, SUNAT).
_FACTORES = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def checksum_ruc(ruc: str) -> bool:
    """Valida el dígito verificador de un RUC (módulo 11). Offline, sin red."""
    if not (isinstance(ruc, str) and ruc.isdigit() and len(ruc) == 11):
        return False
    suma = sum(int(d) * f for d, f in zip(ruc[:10], _FACTORES))
    verif = 11 - (suma % 11)
    if verif == 10:
        return False
    if verif == 11:
        verif = 0
    return verif == int(ruc[10])


@dataclass
class RucData:
    """Resultado de consultar / ficha."""

    ruc: str
    razon_social: Optional[str] = None
    estado: Optional[str] = None
    condicion: Optional[str] = None
    fuente: Optional[str] = None
    actualizado_en: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "RucData":
        return cls(
            ruc=data.get("ruc", ""),
            razon_social=data.get("razon_social"),
            estado=data.get("estado"),
            condicion=data.get("condicion"),
            fuente=data.get("fuente"),
            actualizado_en=data.get("actualizado_en"),
            raw=data,
        )


class ValidaRUC:
    """Cliente mínimo para la API ValidaRUC (vía RapidAPI)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = BASE_URL,
        timeout: int = 15,
    ):
        if not api_key:
            raise ValueError("api_key es obligatoria (tu x-rapidapi-key).")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": RAPIDAPI_HOST,
                "Accept": "application/json",
                "User-Agent": "validaruc-python/0.1.0",
            }
        )

    # -- offline ------------------------------------------------------
    @staticmethod
    def checksum(ruc: str) -> bool:
        """Checksum módulo 11. Gratis, instantáneo, sin red."""
        return checksum_ruc(ruc)

    # -- HTTP helpers -------------------------------------------------
    def _get(self, path: str) -> Dict[str, Any]:
        try:
            res = self._session.get(
                f"{self.base_url}{path}", timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise ValidaRUCError(f"Error de red: {exc}") from exc

        if res.status_code == 404:
            raise RucNoEncontrado("Ese RUC no existe en el padrón.")
        if res.status_code == 429:
            retry = res.headers.get("Retry-After", 60)
            try:
                retry = int(retry)
            except (TypeError, ValueError):
                retry = 60
            raise CuotaSuperada(
                f"Cuota superada, reintenta en {retry}s.", retry_after=retry
            )
        if res.status_code == 403:
            raise ValidaRUCError(
                "Acceso denegado (403). Revisa tu API key."
            )
        if not res.ok:
            raise ValidaRUCError(f"Error {res.status_code} del servicio.")
        try:
            return res.json()
        except ValueError as exc:
            raise ValidaRUCError("Respuesta no-JSON del servicio.") from exc

    def _require_checksum(self, ruc: str) -> None:
        if not checksum_ruc(ruc):
            raise RucInvalido(
                f"RUC {ruc!r} no pasa el checksum módulo 11. "
                "No se hizo ningún request (no se consumió cuota)."
            )

    # -- endpoints ----------------------------------------------------
    def consultar(self, ruc: str) -> RucData:
        """Consulta básica: razón social, estado, condición."""
        self._require_checksum(ruc)
        return RucData.from_json(self._get(f"/v1/ruc/{ruc}"))

    def ficha(self, ruc: str) -> RucData:
        """Ficha completa del padrón (domicilio fiscal, ubigeo, etc.)."""
        self._require_checksum(ruc)
        return RucData.from_json(self._get(f"/v1/ruc/{ruc}/ficha"))

    def health(self) -> Dict[str, Any]:
        """Estado del servicio y frescura de datos. No consume cuota."""
        return self._get("/v1/health")
