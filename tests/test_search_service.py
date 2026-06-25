import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.app.application.search_service import SearchService
from backend.app.domain import GeoPoint, Lead, SearchRequest, SearchResult
from backend.app.services.google_geocoding_service import (
    GoogleGeocodingAddressError,
    GoogleGeocodingNotFoundError,
)
from backend.app.models.cep import CepResponse
from backend.app.services.google_places_service import (
    GooglePlacesUnavailableError,
)
from backend.app.services.viacep_service import ViaCepUnavailableError

ADDRESS = CepResponse(
    cep="12900-000",
    logradouro="Rua José Alves Guedes",
    complemento="",
    bairro="Centro",
    localidade="Bragança Paulista",
    uf="SP",
    ibge="3507605",
    gia="2252",
    ddd="11",
    siafi="6213",
)


def search_request() -> SearchRequest:
    return SearchRequest(
        cep="12900000",
        category="academia",
        radius_km=5,
    )


def test_search_returns_result_with_leads() -> None:
    lead = Lead(
        name="Academia Prospecto",
        city="Bragança Paulista",
        state="SP",
        latitude=-22.953,
        longitude=-46.542,
        source="google_places",
        source_id="place-123",
    )
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    geocoding = AsyncMock()
    geocoding.geocode.return_value = GeoPoint(
        latitude=-22.9527,
        longitude=-46.5419,
    )
    google = AsyncMock()
    google.search_text.return_value = [lead]
    service = SearchService(
        viacep_service=viacep,
        geocoding_service=geocoding,
        google_places_service=google,
    )

    result = asyncio.run(service.search(search_request()))

    assert isinstance(result, SearchResult)
    assert result.origin_cep == "12900000"
    assert result.category == "academia"
    assert result.radius_km == 5
    assert result.total_results == 1
    assert result.leads[0].source_id == "place-123"
    assert result.leads[0].distance_km == pytest.approx(0.035, abs=0.01)
    viacep.lookup.assert_awaited_once_with("12900000")
    geocoding.geocode.assert_awaited_once_with(
        "Rua José Alves Guedes, Centro, Bragança Paulista, "
        "SP, 12900-000, Brasil"
    )
    google.search_text.assert_awaited_once_with(
        "academia",
        origin=GeoPoint(latitude=-22.9527, longitude=-46.5419),
        radius_km=5,
    )


def test_search_returns_empty_result() -> None:
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    geocoding = AsyncMock()
    geocoding.geocode.return_value = GeoPoint(
        latitude=-22.9527,
        longitude=-46.5419,
    )
    google = AsyncMock()
    google.search_text.return_value = []
    service = SearchService(
        viacep_service=viacep,
        geocoding_service=geocoding,
        google_places_service=google,
    )

    result = asyncio.run(service.search(search_request()))

    assert result.total_results == 0
    assert result.leads == []


def test_search_propagates_viacep_failure() -> None:
    viacep = AsyncMock()
    viacep.lookup.side_effect = ViaCepUnavailableError("Falha ViaCEP")
    geocoding = AsyncMock()
    google = AsyncMock()
    service = SearchService(
        viacep_service=viacep,
        geocoding_service=geocoding,
        google_places_service=google,
    )

    with pytest.raises(ViaCepUnavailableError, match="Falha ViaCEP"):
        asyncio.run(service.search(search_request()))

    geocoding.geocode.assert_not_awaited()
    google.search_text.assert_not_awaited()


def test_search_propagates_geocoding_failure() -> None:
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    geocoding = AsyncMock()
    geocoding.geocode.side_effect = GoogleGeocodingNotFoundError(
        "Sem coordenadas"
    )
    google = AsyncMock()
    service = SearchService(
        viacep_service=viacep,
        geocoding_service=geocoding,
        google_places_service=google,
    )

    with pytest.raises(
        GoogleGeocodingNotFoundError,
        match="Sem coordenadas",
    ):
        asyncio.run(service.search(search_request()))

    google.search_text.assert_not_awaited()


def test_search_rejects_address_without_city_and_state() -> None:
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS.model_copy(
        update={"localidade": "", "uf": ""}
    )
    geocoding = AsyncMock()
    google = AsyncMock()
    service = SearchService(
        viacep_service=viacep,
        geocoding_service=geocoding,
        google_places_service=google,
    )

    with pytest.raises(
        GoogleGeocodingAddressError,
        match="dados suficientes",
    ):
        asyncio.run(service.search(search_request()))

    geocoding.geocode.assert_not_awaited()
    google.search_text.assert_not_awaited()


def test_search_propagates_google_places_failure() -> None:
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    geocoding = AsyncMock()
    geocoding.geocode.return_value = GeoPoint(
        latitude=-22.9527,
        longitude=-46.5419,
    )
    google = AsyncMock()
    google.search_text.side_effect = GooglePlacesUnavailableError(
        "Falha Google"
    )
    service = SearchService(
        viacep_service=viacep,
        geocoding_service=geocoding,
        google_places_service=google,
    )

    with pytest.raises(GooglePlacesUnavailableError, match="Falha Google"):
        asyncio.run(service.search(search_request()))


def test_filter_keeps_lead_inside_radius_and_removes_outside() -> None:
    origin = GeoPoint(latitude=-22.9527, longitude=-46.5419)
    inside = Lead(
        name="Dentro",
        latitude=-22.953,
        longitude=-46.542,
    )
    outside = Lead(
        name="Fora",
        latitude=-23.1,
        longitude=-46.7,
    )
    without_coordinates = Lead(name="Sem coordenadas")

    filtered = SearchService.filter_leads_by_radius(
        leads=[inside, outside, without_coordinates],
        origin=origin,
        radius_km=5,
    )

    assert [lead.name for lead in filtered] == ["Dentro"]
    assert filtered[0].distance_km is not None


def test_search_returns_empty_when_no_lead_is_inside_radius() -> None:
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    geocoding = AsyncMock()
    geocoding.geocode.return_value = GeoPoint(
        latitude=-22.9527,
        longitude=-46.5419,
    )
    google = AsyncMock()
    google.search_text.return_value = [
        Lead(
            name="Fora",
            latitude=-23.1,
            longitude=-46.7,
        )
    ]
    service = SearchService(
        viacep_service=viacep,
        geocoding_service=geocoding,
        google_places_service=google,
    )

    result = asyncio.run(service.search(search_request()))

    assert result.total_results == 0
    assert result.leads == []
