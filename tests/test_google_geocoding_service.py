import asyncio

import httpx
import pytest

from backend.app.domain import GeoPoint
from backend.app.services.google_geocoding_service import (
    GoogleGeocodingAuthenticationError,
    GoogleGeocodingConfigurationError,
    GoogleGeocodingNotFoundError,
    GoogleGeocodingService,
    GoogleGeocodingTimeoutError,
    GoogleGeocodingUnavailableError,
)


def run_geocode(
    handler: httpx.AsyncBaseTransport,
    *,
    api_key: str = "test-key",
) -> GeoPoint:
    service = GoogleGeocodingService(
        api_key=api_key,
        transport=handler,
    )
    return asyncio.run(
        service.geocode(
            "Rua José Alves Guedes, Centro, "
            "Bragança Paulista, SP, 12900-000, Brasil"
        )
    )


def test_geocoding_returns_coordinates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/maps/api/geocode/json"
        assert request.url.params["key"] == "test-key"
        assert request.url.params["region"] == "br"
        return httpx.Response(
            200,
            json={
                "status": "OK",
                "results": [
                    {
                        "geometry": {
                            "location": {
                                "lat": -22.9527,
                                "lng": -46.5419,
                            }
                        }
                    }
                ],
            },
        )

    point = run_geocode(httpx.MockTransport(handler))

    assert point == GeoPoint(latitude=-22.9527, longitude=-46.5419)


def test_geocoding_handles_zero_results() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"status": "ZERO_RESULTS", "results": []},
        )
    )

    with pytest.raises(
        GoogleGeocodingNotFoundError,
        match="Nenhuma coordenada",
    ):
        run_geocode(transport)


def test_geocoding_handles_external_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Falha simulada", request=request)

    with pytest.raises(
        GoogleGeocodingUnavailableError,
        match="Não foi possível consultar",
    ):
        run_geocode(httpx.MockTransport(handler))


def test_geocoding_handles_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout simulado", request=request)

    with pytest.raises(
        GoogleGeocodingTimeoutError,
        match="demorou para responder",
    ):
        run_geocode(httpx.MockTransport(handler))


def test_geocoding_handles_denied_request() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"status": "REQUEST_DENIED", "results": []},
        )
    )

    with pytest.raises(
        GoogleGeocodingAuthenticationError,
        match="inválida ou não autorizada",
    ):
        run_geocode(transport)


def test_geocoding_rejects_missing_api_key() -> None:
    transport = httpx.MockTransport(
        lambda request: pytest.fail("Não deveria chamar a API.")
    )

    with pytest.raises(
        GoogleGeocodingConfigurationError,
        match="não está configurada",
    ):
        run_geocode(transport, api_key="")
