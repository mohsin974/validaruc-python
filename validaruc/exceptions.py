"""Excepciones de validaruc."""


class ValidaRUCError(Exception):
    """Error base de ValidaRUC."""


class RucInvalido(ValidaRUCError):
    """El RUC no pasa el checksum módulo 11 (ni se hizo el request)."""


class RucNoEncontrado(ValidaRUCError):
    """El RUC no existe en el padrón SUNAT (HTTP 404)."""


class CuotaSuperada(ValidaRUCError):
    """Cuota del plan superada (HTTP 429)."""

    def __init__(self, message="Cuota superada.", retry_after=60):
        super().__init__(message)
        self.retry_after = retry_after
