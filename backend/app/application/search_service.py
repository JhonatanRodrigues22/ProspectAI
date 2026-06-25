from typing import Protocol

from backend.app.domain import GeoPoint, Lead, SearchRequest, SearchResult
from backend.app.domain.geo import haversine_distance_km
from backend.app.models.cep import CepResponse
from backend.app.services.google_geocoding_service import (
    GoogleGeocodingAddressError,
    GoogleGeocodingService,
)
from backend.app.services.google_places_service import GooglePlacesService
from backend.app.services.viacep_service import ViaCepService


class CepLookup(Protocol):
    async def lookup(self, cep: str) -> CepResponse: ...


class PlacesLookup(Protocol):
    async def search_text(
        self,
        text_query: str,
        *,
        origin: GeoPoint,
        radius_km: float,
    ) -> list[Lead]: ...


class Geocoding(Protocol):
    async def geocode(self, address: str) -> GeoPoint: ...


class SearchService:
    def __init__(
        self,
        *,
        viacep_service: CepLookup,
        geocoding_service: Geocoding,
        google_places_service: PlacesLookup,
    ) -> None:
        self.viacep_service = viacep_service
        self.geocoding_service = geocoding_service
        self.google_places_service = google_places_service

    async def search(self, request: SearchRequest) -> SearchResult:
        address = await self.viacep_service.lookup(request.cep)
        geocoding_address = self.build_geocoding_address(address)
        origin = await self.geocoding_service.geocode(geocoding_address)
        leads = await self.google_places_service.search_text(
            request.category,
            origin=origin,
            radius_km=request.radius_km,
        )
        filtered_leads = self.filter_leads_by_radius(
            leads=leads,
            origin=origin,
            radius_km=request.radius_km,
        )

        return SearchResult(
            origin_cep=request.cep,
            category=request.category,
            radius_km=request.radius_km,
            total_results=len(filtered_leads),
            leads=filtered_leads,
        )

    @staticmethod
    def build_geocoding_address(address: CepResponse) -> str:
        if not address.localidade or not address.uf:
            raise GoogleGeocodingAddressError(
                "O endereço não possui dados suficientes para geocoding."
            )
        parts = [
            address.logradouro,
            address.bairro,
            address.localidade,
            address.uf,
            address.cep,
            "Brasil",
        ]
        return ", ".join(part for part in parts if part)

    @staticmethod
    def filter_leads_by_radius(
        *,
        leads: list[Lead],
        origin: GeoPoint,
        radius_km: float,
    ) -> list[Lead]:
        filtered: list[Lead] = []
        for lead in leads:
            if lead.latitude is None or lead.longitude is None:
                continue
            distance = haversine_distance_km(
                origin,
                GeoPoint(
                    latitude=lead.latitude,
                    longitude=lead.longitude,
                ),
            )
            if distance <= radius_km:
                filtered.append(
                    lead.model_copy(
                        update={"distance_km": round(distance, 3)}
                    )
                )
        return filtered


def get_search_service() -> SearchService:
    return SearchService(
        viacep_service=ViaCepService(),
        geocoding_service=GoogleGeocodingService(),
        google_places_service=GooglePlacesService(),
    )
