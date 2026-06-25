import re

import httpx
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.models.cep import CepResponse


class InvalidCepError(ValueError):
    """O CEP informado não possui um formato aceito."""


class CepNotFoundError(LookupError):
    """O ViaCEP informou que o CEP não existe."""


class ViaCepUnavailableError(RuntimeError):
    """O ViaCEP não pôde responder corretamente."""


class ViaCepTimeoutError(ViaCepUnavailableError):
    """A consulta ao ViaCEP excedeu o tempo limite."""


class ViaCepService:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or settings.viacep_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.viacep_timeout_seconds
        self.transport = transport

    @staticmethod
    def normalize_cep(cep: str) -> str:
        if any(character.isalpha() for character in cep):
            raise InvalidCepError("CEP inválido. Informe exatamente 8 dígitos.")

        normalized_cep = re.sub(r"[^0-9]", "", cep)
        if len(normalized_cep) != 8:
            raise InvalidCepError("CEP inválido. Informe exatamente 8 dígitos.")

        return normalized_cep

    async def lookup(self, cep: str) -> CepResponse:
        normalized_cep = self.normalize_cep(cep)
        url = f"{self.base_url}/ws/{normalized_cep}/json/"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise ViaCepTimeoutError(
                "O ViaCEP demorou para responder. Tente novamente."
            ) from exc
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
            raise ViaCepUnavailableError(
                "Não foi possível consultar o ViaCEP no momento."
            ) from exc

        if not isinstance(payload, dict):
            raise ViaCepUnavailableError(
                "O ViaCEP retornou uma resposta inválida."
            )

        if payload.get("erro") is True:
            raise CepNotFoundError("CEP não encontrado.")

        try:
            return CepResponse.model_validate(payload)
        except ValidationError as exc:
            raise ViaCepUnavailableError(
                "O ViaCEP retornou uma resposta inválida."
            ) from exc


def get_viacep_service() -> ViaCepService:
    return ViaCepService()
