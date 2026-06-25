from typing import Protocol

from backend.app.domain import Lead, SearchRequest, SearchResult
from backend.app.models.cep import CepResponse
from backend.app.services.google_places_service import GooglePlacesService
from backend.app.services.viacep_service import ViaCepService


class CepLookup(Protocol):
    async def lookup(self, cep: str) -> CepResponse: ...


class PlacesLookup(Protocol):
    async def search_text(self, text_query: str) -> list[Lead]: ...


class SearchService:
    def __init__(
        self,
        *,
        viacep_service: CepLookup,
        google_places_service: PlacesLookup,
    ) -> None:
        self.viacep_service = viacep_service
        self.google_places_service = google_places_service

    async def search(self, request: SearchRequest) -> SearchResult:
        address = await self.viacep_service.lookup(request.cep)
        text_query = self.build_text_query(
            category=request.category,
            address=address,
        )
        leads = await self.google_places_service.search_text(text_query)

        return SearchResult(
            origin_cep=request.cep,
            category=request.category,
            radius_km=request.radius_km,
            total_results=len(leads),
            leads=leads,
        )

    @staticmethod
    def build_text_query(
        *,
        category: str,
        address: CepResponse,
    ) -> str:
        location_parts = [
            address.logradouro,
            address.bairro,
            address.localidade,
            address.uf,
        ]
        return ", ".join(
            [category, *(part for part in location_parts if part)]
        )


def get_search_service() -> SearchService:
    return SearchService(
        viacep_service=ViaCepService(),
        google_places_service=GooglePlacesService(),
    )
