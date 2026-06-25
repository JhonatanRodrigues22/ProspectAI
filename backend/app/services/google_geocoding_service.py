import httpx
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.domain import GeoPoint
from backend.app.integrations.google_geocoding.models import (
    GoogleGeocodingResponse,
)


class GoogleGeocodingError(RuntimeError):
    """Erro base da integração Google Geocoding."""


class GoogleGeocodingConfigurationError(GoogleGeocodingError):
    """A integração não possui uma API Key."""


class GoogleGeocodingAddressError(GoogleGeocodingError):
    """O endereço não possui dados suficientes."""


class GoogleGeocodingNotFoundError(GoogleGeocodingError):
    """O endereço não pôde ser geocodificado."""


class GoogleGeocodingAuthenticationError(GoogleGeocodingError):
    """A API Key foi recusada pelo Google."""


class GoogleGeocodingRateLimitError(GoogleGeocodingError):
    """A cota do serviço foi excedida."""


class GoogleGeocodingTimeoutError(GoogleGeocodingError):
    """A chamada excedeu o tempo limite."""


class GoogleGeocodingUnavailableError(GoogleGeocodingError):
    """O serviço não pôde responder corretamente."""


class GoogleGeocodingService:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = (
            settings.google_places_api_key
            if api_key is None
            else api_key
        ).strip()
        self.base_url = (
            base_url or settings.google_geocoding_base_url
        ).rstrip("/")
        self.timeout_seconds = (
            settings.google_geocoding_timeout_seconds
            if timeout_seconds is None
            else timeout_seconds
        )
        self.transport = transport

    async def geocode(self, address: str) -> GeoPoint:
        if not self.api_key:
            raise GoogleGeocodingConfigurationError(
                "A API Key do Google Geocoding não está configurada."
            )
        if not address.strip():
            raise GoogleGeocodingAddressError(
                "O endereço não possui dados suficientes para geocoding."
            )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(
                    f"{self.base_url}/maps/api/geocode/json",
                    params={
                        "address": address.strip(),
                        "key": self.api_key,
                        "region": "br",
                        "language": "pt-BR",
                    },
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise GoogleGeocodingTimeoutError(
                "O Google Geocoding demorou para responder."
            ) from exc
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise GoogleGeocodingUnavailableError(
                "Não foi possível consultar o Google Geocoding."
            ) from exc

        try:
            payload = GoogleGeocodingResponse.model_validate(response.json())
        except (ValidationError, ValueError) as exc:
            raise GoogleGeocodingUnavailableError(
                "O Google Geocoding retornou uma resposta inválida."
            ) from exc

        self._raise_for_status(payload)
        if not payload.results:
            raise GoogleGeocodingNotFoundError(
                "Nenhuma coordenada foi encontrada para o endereço."
            )

        location = payload.results[0].geometry.location
        return GeoPoint(latitude=location.lat, longitude=location.lng)

    @staticmethod
    def _raise_for_status(payload: GoogleGeocodingResponse) -> None:
        if payload.status == "OK":
            return
        if payload.status == "ZERO_RESULTS":
            raise GoogleGeocodingNotFoundError(
                "Nenhuma coordenada foi encontrada para o endereço."
            )
        if payload.status == "OVER_QUERY_LIMIT":
            raise GoogleGeocodingRateLimitError(
                "O limite do Google Geocoding foi atingido."
            )
        if payload.status in {"REQUEST_DENIED", "OVER_DAILY_LIMIT"}:
            raise GoogleGeocodingAuthenticationError(
                "A API Key do Google Geocoding é inválida ou não autorizada."
            )
        raise GoogleGeocodingUnavailableError(
            "O Google Geocoding retornou um erro externo."
        )
