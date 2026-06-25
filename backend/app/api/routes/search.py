from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from backend.app.application.search_service import (
    SearchService,
    get_search_service,
)
from backend.app.domain import SearchRequest, SearchResult
from backend.app.services.google_geocoding_service import (
    GoogleGeocodingAddressError,
    GoogleGeocodingAuthenticationError,
    GoogleGeocodingConfigurationError,
    GoogleGeocodingError,
    GoogleGeocodingNotFoundError,
    GoogleGeocodingRateLimitError,
    GoogleGeocodingTimeoutError,
)
from backend.app.services.google_places_service import (
    GooglePlacesAuthenticationError,
    GooglePlacesConfigurationError,
    GooglePlacesError,
    GooglePlacesRateLimitError,
    GooglePlacesTimeoutError,
)
from backend.app.services.viacep_service import (
    CepNotFoundError,
    InvalidCepError,
    ViaCepService,
    ViaCepTimeoutError,
    ViaCepUnavailableError,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResult)
async def search_leads(
    cep: Annotated[str, Query(description="CEP com ou sem hífen")],
    category: Annotated[str, Query(description="Categoria da empresa")],
    radius_km: Annotated[str, Query(description="Raio em quilômetros")],
    service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResult:
    request = _build_search_request(
        cep=cep,
        category=category,
        radius_km=radius_km,
    )

    try:
        return await service.search(request)
    except CepNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ViaCepTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except ViaCepUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except GoogleGeocodingAddressError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except GoogleGeocodingNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except GoogleGeocodingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GoogleGeocodingAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except GoogleGeocodingRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except GoogleGeocodingTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except GoogleGeocodingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except GooglePlacesConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GooglePlacesAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except GooglePlacesRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except GooglePlacesTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except GooglePlacesError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


def _build_search_request(
    *,
    cep: str,
    category: str,
    radius_km: str,
) -> SearchRequest:
    try:
        normalized_cep = ViaCepService.normalize_cep(cep)
    except InvalidCepError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    try:
        return SearchRequest(
            cep=normalized_cep,
            category=category,
            radius_km=radius_km,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_validation_message(exc),
        ) from exc


def _validation_message(exc: ValidationError) -> str:
    fields = {str(error["loc"][-1]) for error in exc.errors()}
    if "category" in fields:
        return "Categoria inválida. Informe uma categoria não vazia."
    if "radius_km" in fields:
        return "Raio inválido. Informe um valor entre 0 e 50 km."
    return "Parâmetros de busca inválidos."
