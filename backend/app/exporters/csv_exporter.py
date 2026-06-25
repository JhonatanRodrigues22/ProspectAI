import csv
import io

from backend.app.domain import SearchResult
from backend.app.exporters.search_result_rows import (
    EXPORT_HEADERS,
    lead_export_row,
)

CSV_HEADERS = EXPORT_HEADERS


def export_search_result_csv(result: SearchResult) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
    writer.writerow(CSV_HEADERS)

    for lead in result.leads:
        writer.writerow(lead_export_row(lead))

    return output.getvalue().encode("utf-8-sig")
