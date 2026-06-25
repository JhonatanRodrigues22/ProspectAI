import pytest
from pydantic import ValidationError

from backend.app.domain import Lead, SearchRequest, SearchResult


def valid_lead() -> Lead:
    return Lead(
        name="Padaria Prospecto",
        address="Avenida Paulista, 1000",
        city="São Paulo",
        state="SP",
        cep="01310100",
        phone="+55 11 3333-4444",
        whatsapp="+55 11 99999-8888",
        email="contato@example.com",
        website="https://example.com",
        rating=4.7,
        reviews_count=128,
        latitude=-23.561414,
        longitude=-46.655881,
        source="business_directory",
        source_id="place-123",
    )


def test_create_valid_lead() -> None:
    lead = valid_lead()

    assert lead.name == "Padaria Prospecto"
    assert lead.rating == 4.7
    assert lead.reviews_count == 128


def test_reject_lead_with_invalid_rating() -> None:
    with pytest.raises(ValidationError):
        Lead(name="Empresa", rating=5.1)


def test_reject_lead_with_negative_reviews_count() -> None:
    with pytest.raises(ValidationError):
        Lead(name="Empresa", reviews_count=-1)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", -90.1),
        ("latitude", 90.1),
        ("longitude", -180.1),
        ("longitude", 180.1),
    ],
)
def test_reject_lead_with_invalid_coordinates(
    field: str,
    value: float,
) -> None:
    with pytest.raises(ValidationError):
        Lead(name="Empresa", **{field: value})


def test_create_valid_search_request() -> None:
    request = SearchRequest(
        cep="01310100",
        category="padaria",
        radius_km=5,
    )

    assert request.cep == "01310100"
    assert request.category == "padaria"
    assert request.radius_km == 5


def test_reject_search_request_with_invalid_radius() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(
            cep="01310100",
            category="padaria",
            radius_km=0,
        )


def test_reject_search_request_above_supported_radius() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(
            cep="01310100",
            category="padaria",
            radius_km=50.1,
        )


def test_reject_search_request_with_empty_category() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(
            cep="01310100",
            category="   ",
            radius_km=5,
        )


def test_create_search_result_with_leads() -> None:
    lead = valid_lead()

    result = SearchResult(
        origin_cep="01310100",
        category="padaria",
        radius_km=5,
        total_results=1,
        leads=[lead],
    )

    assert result.total_results == 1
    assert result.leads == [lead]


@pytest.mark.parametrize("cep", ["01310-100", "0131010", "0131010A"])
def test_domain_models_require_normalized_cep(cep: str) -> None:
    with pytest.raises(ValidationError):
        SearchRequest(cep=cep, category="padaria", radius_km=5)
