import httpx
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.domain import GeoPoint, Lead
from backend.app.integrations.google_places.mapper import (
    GooglePlaceMappingError,
    map_google_place_to_lead,
)
from backend.app.integrations.google_places.models import GooglePlacesResponse

GOOGLE_PLACES_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.addressComponents",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
        "places.location",
    ]
)


class GooglePlacesError(RuntimeError):
    """Erro base da integração com Google Places."""


class GooglePlacesConfigurationError(GooglePlacesError):
    """A integração não possui configuração válida."""


class GooglePlacesAuthenticationError(GooglePlacesError):
    """A API Key foi recusada pelo Google Places."""


class GooglePlacesRateLimitError(GooglePlacesError):
    """A cota ou o limite de requisições foi excedido."""


class GooglePlacesTimeoutError(GooglePlacesError):
    """A chamada ao Google Places excedeu o tempo limite."""


class GooglePlacesUnavailableError(GooglePlacesError):
    """O Google Places não pôde responder corretamente."""


class GooglePlacesService:
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
            base_url or settings.google_places_base_url
        ).rstrip("/")
        self.timeout_seconds = (
            settings.google_places_timeout_seconds
            if timeout_seconds is None
            else timeout_seconds
        )
        self.transport = transport

    async def search_text(
        self,
        text_query: str,
        *,
        origin: GeoPoint | None = None,
        radius_km: float | None = None,
        max_result_count: int = 20,
    ) -> list[Lead]:
        if not self.api_key:
            raise GooglePlacesConfigurationError(
                "A API Key do Google Places não está configurada."
            )

        query = text_query.strip()
        if not query:
            raise ValueError("A consulta do Google Places não pode ser vazia.")
        if not 1 <= max_result_count <= 20:
            raise ValueError(
                "A quantidade de resultados deve estar entre 1 e 20."
            )
        if (origin is None) != (radius_km is None):
            raise ValueError(
                "Origem e raio devem ser informados em conjunto."
            )
        if radius_km is not None and not 0 < radius_km <= 50:
            raise ValueError("O raio deve estar entre 0 e 50 km.")

        request_body: dict[str, object] = {
            "textQuery": query,
            "pageSize": max_result_count,
        }
        if origin is not None and radius_km is not None:
            request_body["locationBias"] = {
                "circle": {
                    "center": origin.model_dump(),
                    "radius": radius_km * 1000,
                }
            }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/v1/places:searchText",
                    headers={
                        "X-Goog-Api-Key": self.api_key,
                        "X-Goog-FieldMask": GOOGLE_PLACES_FIELD_MASK,
                    },
                    json=request_body,
                )
                self._raise_for_status(response)
        except httpx.TimeoutException as exc:
            raise GooglePlacesTimeoutError(
                "O Google Places demorou para responder. Tente novamente."
            ) from exc
        except GooglePlacesError:
            raise
        except httpx.RequestError as exc:
            raise GooglePlacesUnavailableError(
                "Não foi possível consultar o Google Places no momento."
            ) from exc

        try:
            payload = response.json()
            google_response = GooglePlacesResponse.model_validate(payload)
            return [
                map_google_place_to_lead(place)
                for place in google_response.places
            ]
        except (ValidationError, GooglePlaceMappingError, ValueError) as exc:
            raise GooglePlacesUnavailableError(
                "O Google Places retornou uma resposta inválida."
            ) from exc

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code in {401, 403} or (
            response.status_code == 400
            and GooglePlacesService._is_api_key_error(response)
        ):
            raise GooglePlacesAuthenticationError(
                "A API Key do Google Places é inválida ou não autorizada."
            )
        if response.status_code == 429:
            raise GooglePlacesRateLimitError(
                "O limite de consultas do Google Places foi atingido."
            )
        if response.is_error:
            raise GooglePlacesUnavailableError(
                "O Google Places retornou um erro externo."
            )

    @staticmethod
    def _is_api_key_error(response: httpx.Response) -> bool:
        try:
            error_payload = response.json().get("error", {})
        except (ValueError, AttributeError):
            return False

        message = str(error_payload.get("message", "")).lower()
        details = str(error_payload.get("details", "")).lower()
        return "api key" in message or "api_key" in details
