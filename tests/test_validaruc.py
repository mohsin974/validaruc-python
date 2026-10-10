"""Tests de validaruc — checksum real + HTTP con mocks."""

from unittest.mock import Mock, patch

import pytest
import requests

from validaruc import (
    CuotaSuperada,
    RucData,
    RucInvalido,
    RucNoEncontrado,
    ValidaRUC,
    ValidaRUCError,
    checksum_ruc,
)


# -- checksum (puro, sin red) ------------------------------------------
def test_checksum_valido():
    assert checksum_ruc("10452159428") is True


def test_checksum_digito_mal():
    assert checksum_ruc("10452159429") is False


def test_checksum_corto():
    assert checksum_ruc("1234567") is False


def test_checksum_no_numerico():
    assert checksum_ruc("1045215942a") is False


def test_checksum_vacio():
    assert checksum_ruc("") is False


def test_checksum_via_metodo():
    assert ValidaRUC.checksum("10452159428") is True


# -- consultar: checksum primero, sin request ---------------------------
def _client():
    return ValidaRUC(api_key="TESTKEY")


def test_consultar_ruc_invalido_no_hace_request():
    api = _client()
    with patch.object(api._session, "get") as get:
        with pytest.raises(RucInvalido):
            api.consultar("1234567")
        get.assert_not_called()


def _resp(status=200, json_data=None, headers=None):
    r = Mock()
    r.status_code = status
    r.ok = 200 <= status < 300
    r.headers = headers or {}
    r.json = Mock(return_value=json_data or {})
    return r


def test_consultar_ok():
    api = _client()
    payload = {
        "ruc": "10452159428",
        "razon_social": "GARCIA CHANCO CARLOS AUGUSTO",
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "fuente": "SUNAT Padrón Reducido",
        "actualizado_en": "2026-10-09",
    }
    with patch.object(api._session, "get", return_value=_resp(200, payload)) as get:
        r = api.consultar("10452159428")
        assert isinstance(r, RucData)
        assert r.razon_social == "GARCIA CHANCO CARLOS AUGUSTO"
        assert r.estado == "ACTIVO"
        assert r.actualizado_en == "2026-10-09"
        get.assert_called_once()
        url = get.call_args[0][0]
        assert url.endswith("/v1/ruc/10452159428")


def test_consultar_404():
    api = _client()
    with patch.object(api._session, "get", return_value=_resp(404)):
        with pytest.raises(RucNoEncontrado):
            api.consultar("10452159428")


def test_consultar_429_con_retry_after():
    api = _client()
    with patch.object(
        api._session, "get", return_value=_resp(429, headers={"Retry-After": "60"})
    ):
        with pytest.raises(CuotaSuperada) as exc:
            api.consultar("10452159428")
        assert exc.value.retry_after == 60


def test_ficha_ok():
    api = _client()
    payload = {"ruc": "10452159428", "razon_social": "X", "ficha": True}
    with patch.object(api._session, "get", return_value=_resp(200, payload)) as get:
        r = api.ficha("10452159428")
        assert r.raw.get("ficha") is True
        assert get.call_args[0][0].endswith("/v1/ruc/10452159428/ficha")


def test_health_no_requiere_checksum():
    api = _client()
    payload = {"status": "ok"}
    with patch.object(api._session, "get", return_value=_resp(200, payload)) as get:
        assert api.health() == {"status": "ok"}
        assert get.call_args[0][0].endswith("/v1/health")


def test_error_de_red():
    api = _client()
    with patch.object(
        api._session, "get", side_effect=requests.ConnectionError("down")
    ):
        with pytest.raises(ValidaRUCError):
            api.consultar("10452159428")


def test_api_key_obligatoria():
    with pytest.raises(ValueError):
        ValidaRUC(api_key="")
