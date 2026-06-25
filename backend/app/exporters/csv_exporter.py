import csv
import io

from backend.app.domain import Lead, SearchResult

CSV_HEADERS = [
    "Nome da empresa",
    "Telefone",
    "WhatsApp",
    "E-mail",
    "Site",
    "Endereço",
    "Cidade",
    "Estado",
    "CEP",
    "Nota",
    "Quantidade de avaliações",
    "Distância em km",
    "Fonte",
    "ID da fonte",
]


def export_search_result_csv(result: SearchResult) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
    writer.writerow(CSV_HEADERS)

    for lead in result.leads:
        writer.writerow(_lead_row(lead))

    return output.getvalue().encode("utf-8-sig")


def _lead_row(lead: Lead) -> list[object]:
    return [
        lead.name,
        lead.phone or "",
        lead.whatsapp or "",
        lead.email or "",
        lead.website or "",
        lead.address or "",
        lead.city or "",
        lead.state or "",
        lead.cep or "",
        _optional_number(lead.rating),
        lead.reviews_count,
        _optional_number(lead.distance_km),
        lead.source or "",
        lead.source_id or "",
    ]


def _optional_number(value: float | None) -> float | str:
    return "" if value is None else value
