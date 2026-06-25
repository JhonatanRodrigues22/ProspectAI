import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.app.application.search_service import SearchService
from backend.app.domain import Lead, SearchRequest, SearchResult
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
        source="google_places",
        source_id="place-123",
    )
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    google = AsyncMock()
    google.search_text.return_value = [lead]
    service = SearchService(
        viacep_service=viacep,
        google_places_service=google,
    )

    result = asyncio.run(service.search(search_request()))

    assert isinstance(result, SearchResult)
    assert result.origin_cep == "12900000"
    assert result.category == "academia"
    assert result.radius_km == 5
    assert result.total_results == 1
    assert result.leads == [lead]
    viacep.lookup.assert_awaited_once_with("12900000")
    google.search_text.assert_awaited_once_with(
        "academia, Rua José Alves Guedes, Centro, "
        "Bragança Paulista, SP"
    )


def test_search_returns_empty_result() -> None:
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    google = AsyncMock()
    google.search_text.return_value = []
    service = SearchService(
        viacep_service=viacep,
        google_places_service=google,
    )

    result = asyncio.run(service.search(search_request()))

    assert result.total_results == 0
    assert result.leads == []


def test_search_propagates_viacep_failure() -> None:
    viacep = AsyncMock()
    viacep.lookup.side_effect = ViaCepUnavailableError("Falha ViaCEP")
    google = AsyncMock()
    service = SearchService(
        viacep_service=viacep,
        google_places_service=google,
    )

    with pytest.raises(ViaCepUnavailableError, match="Falha ViaCEP"):
        asyncio.run(service.search(search_request()))

    google.search_text.assert_not_awaited()


def test_search_propagates_google_places_failure() -> None:
    viacep = AsyncMock()
    viacep.lookup.return_value = ADDRESS
    google = AsyncMock()
    google.search_text.side_effect = GooglePlacesUnavailableError(
        "Falha Google"
    )
    service = SearchService(
        viacep_service=viacep,
        google_places_service=google,
    )

    with pytest.raises(GooglePlacesUnavailableError, match="Falha Google"):
        asyncio.run(service.search(search_request()))


def test_text_query_omits_missing_optional_address_parts() -> None:
    address = ADDRESS.model_copy(
        update={"logradouro": "", "bairro": ""}
    )

    query = SearchService.build_text_query(
        category="academia",
        address=address,
    )

    assert query == "academia, Bragança Paulista, SP"
