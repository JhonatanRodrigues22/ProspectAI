import csv
import io

from backend.app.domain import Lead, SearchResult
from backend.app.exporters import export_search_result_csv
from backend.app.exporters.csv_exporter import CSV_HEADERS


def search_result(leads: list[Lead]) -> SearchResult:
    return SearchResult(
        origin_cep="01310100",
        category="cafeteria",
        radius_km=5,
        total_results=len(leads),
        leads=leads,
    )


def read_csv(content: bytes) -> list[list[str]]:
    text = content.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text), delimiter=";"))


def test_export_search_result_with_leads() -> None:
    lead = Lead(
        name="Café São José",
        phone="+55 11 3333-4444",
        whatsapp="+55 11 99999-8888",
        email="contato@cafe.com",
        website="https://cafe.com",
        address="Avenida Paulista, 1000",
        city="São Paulo",
        state="SP",
        cep="01310100",
        rating=4.8,
        reviews_count=120,
        distance_km=1.234,
        source="google_places",
        source_id="place-123",
    )

    rows = read_csv(export_search_result_csv(search_result([lead])))

    assert rows[0] == CSV_HEADERS
    assert rows[1] == [
        "Café São José",
        "+55 11 3333-4444",
        "+55 11 99999-8888",
        "contato@cafe.com",
        "https://cafe.com",
        "Avenida Paulista, 1000",
        "São Paulo",
        "SP",
        "01310100",
        "4.8",
        "120",
        "1.234",
        "google_places",
        "place-123",
    ]


def test_export_empty_result_contains_headers_only() -> None:
    rows = read_csv(export_search_result_csv(search_result([])))

    assert rows == [CSV_HEADERS]


def test_export_preserves_accents_and_uses_utf8_bom() -> None:
    content = export_search_result_csv(
        search_result([Lead(name="Café Açúcar")])
    )

    assert content.startswith(b"\xef\xbb\xbf")
    assert "Café Açúcar" in content.decode("utf-8-sig")


def test_export_writes_missing_fields_as_empty() -> None:
    rows = read_csv(
        export_search_result_csv(search_result([Lead(name="Empresa")]))
    )

    assert rows[1] == [
        "Empresa",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "0",
        "",
        "",
        "",
    ]


def test_export_is_compatible_with_standard_csv_reader() -> None:
    lead = Lead(
        name='Empresa "Especial"; Comércio',
        address="Rua A; 10",
    )

    rows = read_csv(export_search_result_csv(search_result([lead])))

    assert rows[1][0] == 'Empresa "Especial"; Comércio'
    assert rows[1][5] == "Rua A; 10"
