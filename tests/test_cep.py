import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.viacep_service import ViaCepService, get_viacep_service

VALID_RESPONSE = {
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "complemento": "até 610 - lado par",
    "bairro": "Bela Vista",
    "localidade": "São Paulo",
    "uf": "SP",
    "ibge": "3550308",
    "gia": "1004",
    "ddd": "11",
    "siafi": "7107",
}


def client_with_handler(
    handler: httpx.AsyncBaseTransport,
) -> TestClient:
    app.dependency_overrides[get_viacep_service] = lambda: ViaCepService(
        transport=handler
    )
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize("cep", ["01310-100", "01310100"])
def test_lookup_valid_cep_with_or_without_hyphen(cep: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/ws/01310100/json/"
        return httpx.Response(200, json=VALID_RESPONSE)

    client = client_with_handler(httpx.MockTransport(handler))

    response = client.get(f"/api/cep/{cep}")

    assert response.status_code == 200
    assert response.json() == VALID_RESPONSE


def test_lookup_rejects_cep_with_fewer_than_eight_digits() -> None:
    client = TestClient(app)

    response = client.get("/api/cep/1234567")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "CEP inválido. Informe exatamente 8 dígitos."
    }


@pytest.mark.parametrize("cep", ["01310A100", "01310ç100"])
def test_lookup_rejects_cep_with_letters(cep: str) -> None:
    client = TestClient(app)

    response = client.get(f"/api/cep/{cep}")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "CEP inválido. Informe exatamente 8 dígitos."
    }


def test_lookup_returns_not_found_for_unknown_cep() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"erro": True})

    client = client_with_handler(httpx.MockTransport(handler))

    response = client.get("/api/cep/00000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "CEP não encontrado."}


def test_lookup_handles_external_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Falha simulada", request=request)

    client = client_with_handler(httpx.MockTransport(handler))

    response = client.get("/api/cep/01310100")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Não foi possível consultar o ViaCEP no momento."
    }


def test_lookup_handles_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout simulado", request=request)

    client = client_with_handler(httpx.MockTransport(handler))

    response = client.get("/api/cep/01310100")

    assert response.status_code == 504
    assert response.json() == {
        "detail": "O ViaCEP demorou para responder. Tente novamente."
    }


def test_lookup_handles_malformed_external_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = client_with_handler(httpx.MockTransport(handler))

    response = client.get("/api/cep/01310100")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "O ViaCEP retornou uma resposta inválida."
    }
