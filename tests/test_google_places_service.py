import asyncio
import json

import httpx
import pytest

from backend.app.domain import GeoPoint, Lead
from backend.app.services.google_places_service import (
    GOOGLE_PLACES_FIELD_MASK,
    GooglePlacesAuthenticationError,
    GooglePlacesConfigurationError,
    GooglePlacesRateLimitError,
    GooglePlacesService,
    GooglePlacesTimeoutError,
    GooglePlacesUnavailableError,
)

VALID_RESPONSE = {
    "places": [
        {
            "id": "place-123",
            "displayName": {"text": "Padaria Prospecto"},
            "formattedAddress": "Avenida Paulista, 1000 - São Paulo, SP",
            "addressComponents": [
                {
                    "longText": "São Paulo",
                    "shortText": "São Paulo",
                    "types": ["locality"],
                },
                {
                    "longText": "São Paulo",
                    "shortText": "SP",
                    "types": ["administrative_area_level_1"],
                },
                {
                    "longText": "01310-100",
                    "shortText": "01310-100",
                    "types": ["postal_code"],
                },
            ],
            "internationalPhoneNumber": "+55 11 3333-4444",
            "websiteUri": "https://example.com",
            "rating": 4.7,
            "userRatingCount": 128,
            "location": {
                "latitude": -23.561414,
                "longitude": -46.655881,
            },
        }
    ]
}


def run_search(
    handler: httpx.AsyncBaseTransport,
    *,
    api_key: str = "test-key",
) -> list[Lead]:
    service = GooglePlacesService(
        api_key=api_key,
        transport=handler,
    )
    return asyncio.run(service.search_text("padaria em São Paulo"))


def test_maps_valid_response_to_leads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/places:searchText"
        assert request.headers["X-Goog-Api-Key"] == "test-key"
        assert request.headers["X-Goog-FieldMask"] == GOOGLE_PLACES_FIELD_MASK
        assert json.loads(request.content) == {
            "textQuery": "padaria em São Paulo",
            "pageSize": 20,
        }
        return httpx.Response(200, json=VALID_RESPONSE)

    leads = run_search(httpx.MockTransport(handler))

    assert len(leads) == 1
    lead = leads[0]
    assert lead.name == "Padaria Prospecto"
    assert lead.city == "São Paulo"
    assert lead.state == "SP"
    assert lead.cep == "01310100"
    assert lead.phone == "+55 11 3333-4444"
    assert lead.website == "https://example.com"
    assert lead.rating == 4.7
    assert lead.reviews_count == 128
    assert lead.latitude == -23.561414
    assert lead.longitude == -46.655881
    assert lead.source == "google_places"
    assert lead.source_id == "place-123"


def test_returns_empty_list() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"places": []})
    )

    assert run_search(transport) == []


def test_sends_location_bias_with_origin_and_radius() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["locationBias"] == {
            "circle": {
                "center": {
                    "latitude": -22.9527,
                    "longitude": -46.5419,
                },
                "radius": 5000,
            }
        }
        return httpx.Response(200, json={"places": []})

    service = GooglePlacesService(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    leads = asyncio.run(
        service.search_text(
            "academia",
            origin=GeoPoint(latitude=-22.9527, longitude=-46.5419),
            radius_km=5,
        )
    )

    assert leads == []


def test_handles_invalid_api_key() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(403, json={"error": {}})
    )

    with pytest.raises(
        GooglePlacesAuthenticationError,
        match="inválida ou não autorizada",
    ):
        run_search(transport)


def test_handles_invalid_api_key_reported_as_bad_request() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            400,
            json={
                "error": {
                    "message": "API key not valid.",
                    "details": [{"reason": "API_KEY_INVALID"}],
                }
            },
        )
    )

    with pytest.raises(
        GooglePlacesAuthenticationError,
        match="inválida ou não autorizada",
    ):
        run_search(transport)


def test_handles_rate_limit() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, json={"error": {}})
    )

    with pytest.raises(
        GooglePlacesRateLimitError,
        match="limite de consultas",
    ):
        run_search(transport)


def test_handles_http_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500, json={"error": {}})
    )

    with pytest.raises(
        GooglePlacesUnavailableError,
        match="erro externo",
    ):
        run_search(transport)


def test_handles_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout simulado", request=request)

    with pytest.raises(
        GooglePlacesTimeoutError,
        match="demorou para responder",
    ):
        run_search(httpx.MockTransport(handler))


def test_handles_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Falha simulada", request=request)

    with pytest.raises(
        GooglePlacesUnavailableError,
        match="Não foi possível consultar",
    ):
        run_search(httpx.MockTransport(handler))


def test_rejects_missing_api_key_before_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("A requisição não deveria ser executada.")

    with pytest.raises(
        GooglePlacesConfigurationError,
        match="não está configurada",
    ):
        run_search(httpx.MockTransport(handler), api_key="")


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"places": [{"id": "place-without-name"}]},
        {"places": "invalid"},
    ],
)
def test_handles_malformed_response(payload: object) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload)
    )

    with pytest.raises(
        GooglePlacesUnavailableError,
        match="resposta inválida",
    ):
        run_search(transport)


def test_handles_invalid_json_response() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"not-json")
    )

    with pytest.raises(
        GooglePlacesUnavailableError,
        match="resposta inválida",
    ):
        run_search(transport)


def test_maps_missing_optional_fields_to_none() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "places": [
                    {
                        "id": "minimal-place",
                        "displayName": {"text": "Empresa mínima"},
                    }
                ]
            },
        )
    )

    lead = run_search(transport)[0]

    assert lead.name == "Empresa mínima"
    assert lead.address is None
    assert lead.city is None
    assert lead.state is None
    assert lead.cep is None
    assert lead.phone is None
    assert lead.website is None
    assert lead.rating is None
    assert lead.reviews_count == 0
    assert lead.latitude is None
    assert lead.longitude is None
