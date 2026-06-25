from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.models.cep import CepResponse
from backend.app.services.viacep_service import (
    CepNotFoundError,
    InvalidCepError,
    ViaCepService,
    ViaCepTimeoutError,
    ViaCepUnavailableError,
    get_viacep_service,
)

router = APIRouter(prefix="/cep", tags=["cep"])


@router.get("/{cep}", response_model=CepResponse)
async def lookup_cep(
    cep: str,
    service: Annotated[ViaCepService, Depends(get_viacep_service)],
) -> CepResponse:
    try:
        return await service.lookup(cep)
    except InvalidCepError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
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
