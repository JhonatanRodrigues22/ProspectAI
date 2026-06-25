import asyncio
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from backend.app.domain import InvalidCepError, Lead, SearchResult
from ui.streamlit_app import execute_search, leads_to_rows


def test_streamlit_app_renders_search_form() -> None:
    app = AppTest.from_file("ui/streamlit_app.py")

    app.run()

    assert not app.exception
    assert app.title[0].value == "ProspectAI"
    assert app.text_input[0].label == "CEP"
    assert app.text_input[1].label == "Categoria"
    assert app.number_input[0].label == "Raio (km)"
    assert app.button[0].label == "Pesquisar"


def test_streamlit_app_displays_completed_search() -> None:
    service = AsyncMock()
    service.search.return_value = SearchResult(
        origin_cep="12900000",
        category="academia",
        radius_km=5,
        total_results=1,
        leads=[Lead(name="Academia Prospecto", distance_km=1.2)],
    )
    app = AppTest.from_file("ui/streamlit_app.py")
    app.session_state["_search_service_override"] = service

    app.run()
    app.text_input[0].set_value("12900-000")
    app.text_input[1].set_value("academia")
    app.number_input[0].set_value(5)
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert app.success[0].value == "Busca concluída: 1 resultado(s)."
    assert len(app.dataframe) == 1
    assert len(app.get("download_button")) == 2


def test_streamlit_app_displays_empty_state() -> None:
    service = AsyncMock()
    service.search.return_value = SearchResult(
        origin_cep="12900000",
        category="academia",
        radius_km=5,
        total_results=0,
        leads=[],
    )
    app = AppTest.from_file("ui/streamlit_app.py")
    app.session_state["_search_service_override"] = service

    app.run()
    app.text_input[0].set_value("12900000")
    app.text_input[1].set_value("academia")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert app.info[0].value == (
        "Nenhum resultado encontrado para os critérios informados."
    )
    assert len(app.get("download_button")) == 0


def test_streamlit_app_displays_error_state() -> None:
    service = AsyncMock()
    service.search.side_effect = RuntimeError("Falha simulada")
    app = AppTest.from_file("ui/streamlit_app.py")
    app.session_state["_search_service_override"] = service

    app.run()
    app.text_input[0].set_value("12900000")
    app.text_input[1].set_value("academia")
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert app.error[0].value == (
        "Não foi possível concluir a pesquisa. Tente novamente."
    )


def test_execute_search_calls_search_service_with_domain_request() -> None:
    result = SearchResult(
        origin_cep="12900000",
        category="academia",
        radius_km=5,
        total_results=0,
        leads=[],
    )
    search = AsyncMock(return_value=result)

    returned = execute_search(
        cep="12900-000",
        category="academia",
        radius_km=5,
        search=search,
    )

    assert returned == result
    request = search.await_args.args[0]
    assert request.cep == "12900000"
    assert request.category == "academia"
    assert request.radius_km == 5


def test_execute_search_rejects_invalid_cep() -> None:
    search = AsyncMock()

    with pytest.raises(InvalidCepError):
        execute_search(
            cep="123",
            category="academia",
            radius_km=5,
            search=search,
        )

    search.assert_not_awaited()


def test_execute_search_rejects_empty_category() -> None:
    search = AsyncMock()

    with pytest.raises(ValidationError):
        execute_search(
            cep="12900000",
            category=" ",
            radius_km=5,
            search=search,
        )

    search.assert_not_awaited()


def test_leads_to_rows_prepares_table_data() -> None:
    lead = Lead(
        name="Academia Prospecto",
        city="Bragança Paulista",
        state="SP",
        phone="+55 11 3333-4444",
        rating=4.8,
        reviews_count=120,
        distance_km=1.234,
    )

    rows = leads_to_rows([lead])

    assert rows == [
        {
            "Nome": "Academia Prospecto",
            "Endereço": "",
            "Cidade": "Bragança Paulista",
            "UF": "SP",
            "CEP": "",
            "Telefone": "+55 11 3333-4444",
            "WhatsApp": "",
            "E-mail": "",
            "Website": "",
            "Avaliação": 4.8,
            "Reviews": 120,
            "Distância (km)": 1.234,
        }
    ]
