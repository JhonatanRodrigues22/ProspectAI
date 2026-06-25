import asyncio
from collections.abc import Awaitable, Callable

import streamlit as st
from pydantic import ValidationError

from backend.app.application.search_service import (
    SearchService,
    get_search_service,
)
from backend.app.domain import (
    InvalidCepError,
    Lead,
    SearchRequest,
    SearchResult,
    normalize_cep,
)
from backend.app.exporters import export_search_result_csv

SearchRunner = Callable[[SearchRequest], Awaitable[SearchResult]]


def execute_search(
    *,
    cep: str,
    category: str,
    radius_km: float,
    search: SearchRunner,
) -> SearchResult:
    normalized_cep = normalize_cep(cep)
    request = SearchRequest(
        cep=normalized_cep,
        category=category,
        radius_km=radius_km,
    )
    return asyncio.run(search(request))


def leads_to_rows(leads: list[Lead]) -> list[dict[str, object]]:
    return [
        {
            "Nome": lead.name,
            "Endereço": lead.address or "",
            "Cidade": lead.city or "",
            "UF": lead.state or "",
            "CEP": lead.cep or "",
            "Telefone": lead.phone or "",
            "WhatsApp": lead.whatsapp or "",
            "E-mail": lead.email or "",
            "Website": lead.website or "",
            "Avaliação": lead.rating,
            "Reviews": lead.reviews_count,
            "Distância (km)": lead.distance_km,
        }
        for lead in leads
    ]


def render_app(service: SearchService | None = None) -> None:
    st.set_page_config(page_title="ProspectAI", page_icon="🔎", layout="wide")
    st.title("ProspectAI")
    st.caption("Encontre empresas por CEP, categoria e raio.")

    with st.form("search_form"):
        cep = st.text_input(
            "CEP",
            placeholder="Ex.: 12900-000",
        )
        category = st.text_input(
            "Categoria",
            placeholder="Ex.: academia",
        )
        radius_km = st.number_input(
            "Raio (km)",
            min_value=0.1,
            max_value=50.0,
            value=5.0,
            step=0.5,
        )
        submitted = st.form_submit_button(
            "Pesquisar",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return

    search_service = (
        service
        or st.session_state.get("_search_service_override")
        or get_search_service()
    )

    try:
        with st.spinner("Pesquisando empresas..."):
            result = execute_search(
                cep=cep,
                category=category,
                radius_km=radius_km,
                search=search_service.search,
            )
    except (InvalidCepError, ValidationError) as exc:
        st.error(_validation_message(exc))
        return
    except Exception:
        st.error("Não foi possível concluir a pesquisa. Tente novamente.")
        return

    if not result.leads:
        st.info("Nenhum resultado encontrado para os critérios informados.")
        return

    st.success(f"Busca concluída: {result.total_results} resultado(s).")
    st.dataframe(
        leads_to_rows(result.leads),
        hide_index=True,
        width="stretch",
    )
    st.download_button(
        "Baixar CSV",
        data=export_search_result_csv(result),
        file_name=_csv_filename(result),
        mime="text/csv; charset=utf-8",
        width="stretch",
    )


def _validation_message(exc: Exception) -> str:
    if isinstance(exc, InvalidCepError):
        return str(exc)
    if isinstance(exc, ValidationError):
        fields = {str(error["loc"][-1]) for error in exc.errors()}
        if "category" in fields:
            return "Categoria inválida. Informe uma categoria não vazia."
        if "radius_km" in fields:
            return "Raio inválido. Informe um valor entre 0 e 50 km."
    return "Dados de busca inválidos."


def _csv_filename(result: SearchResult) -> str:
    safe_category = "".join(
        character if character.isalnum() else "_"
        for character in result.category.lower()
    ).strip("_")
    return f"prospectai_{safe_category or 'resultados'}_{result.origin_cep}.csv"


if __name__ == "__main__":
    render_app()
