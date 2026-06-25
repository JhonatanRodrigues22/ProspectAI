from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.app.application.search_service import get_search_service
from backend.app.domain import Lead, SearchResult
from backend.app.main import app
from backend.app.services.google_geocoding_service import (
    GoogleGeocodingAddressError,
    GoogleGeocodingNotFoundError,
    GoogleGeocodingUnavailableError,
)
from backend.app.services.google_places_service import (
    GooglePlacesConfigurationError,
    GooglePlacesUnavailableError,
)
from backend.app.services.viacep_service import (
    CepNotFoundError,
    ViaCepUnavailableError,
)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def client_with_search_result(
    result: SearchResult | None = None,
    *,
    error: Exception | None = None,
) -> tuple[TestClient, AsyncMock]:
    service = AsyncMock()
    if error:
        service.search.side_effect = error
    else:
        service.search.return_value = result
    app.dependency_overrides[get_search_service] = lambda: service
    return TestClient(app), service


def test_search_endpoint_returns_results() -> None:
    lead = Lead(name="Academia Prospecto", source="google_places")
    result = SearchResult(
        origin_cep="12900000",
        category="academia",
        radius_km=5,
        total_results=1,
        leads=[lead],
    )
    client, service = client_with_search_result(result)

    response = client.get(
        "/api/search",
        params={
            "cep": "12900-000",
            "category": "academia",
            "radius_km": "5",
        },
    )

    assert response.status_code == 200
    assert response.json()["total_results"] == 1
    request = service.search.await_args.args[0]
    assert request.cep == "12900000"
    assert request.category == "academia"
    assert request.radius_km == 5


def test_search_endpoint_returns_empty_result() -> None:
    result = SearchResult(
        origin_cep="12900000",
        category="academia",
        radius_km=5,
        total_results=0,
        leads=[],
    )
    client, _ = client_with_search_result(result)

    response = client.get(
        "/api/search?cep=12900000&category=academia&radius_km=5"
    )

    assert response.status_code == 200
    assert response.json()["leads"] == []
    assert response.json()["total_results"] == 0


@pytest.mark.parametrize("cep", ["1234567", "12900A000"])
def test_search_endpoint_rejects_invalid_cep(cep: str) -> None:
    client, service = client_with_search_result()

    response = client.get(
        "/api/search",
        params={"cep": cep, "category": "academia", "radius_km": "5"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "CEP inválido. Informe exatamente 8 dígitos."
    }
    service.search.assert_not_awaited()


def test_search_endpoint_rejects_empty_category() -> None:
    client, service = client_with_search_result()

    response = client.get(
        "/api/search",
        params={"cep": "12900000", "category": " ", "radius_km": "5"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Categoria inválida. Informe uma categoria não vazia."
    }
    service.search.assert_not_awaited()


@pytest.mark.parametrize("radius", ["0", "-1", "51", "abc"])
def test_search_endpoint_rejects_invalid_radius(radius: str) -> None:
    client, service = client_with_search_result()

    response = client.get(
        "/api/search",
        params={
            "cep": "12900000",
            "category": "academia",
            "radius_km": radius,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Raio inválido. Informe um valor entre 0 e 50 km."
    }
    service.search.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (CepNotFoundError("CEP não encontrado."), 404),
        (ViaCepUnavailableError("Falha ViaCEP"), 502),
        (GoogleGeocodingAddressError("Endereço insuficiente"), 422),
        (GoogleGeocodingNotFoundError("Sem coordenadas"), 404),
        (GoogleGeocodingUnavailableError("Falha geocoding"), 502),
        (GooglePlacesConfigurationError("API Key ausente"), 503),
        (GooglePlacesUnavailableError("Falha Google"), 502),
    ],
)
def test_search_endpoint_translates_external_errors(
    error: Exception,
    status_code: int,
) -> None:
    client, _ = client_with_search_result(error=error)

    response = client.get(
        "/api/search?cep=12900000&category=academia&radius_km=5"
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": str(error)}
