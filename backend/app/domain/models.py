from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NormalizedCep = Annotated[
    str,
    StringConstraints(pattern=r"^\d{8}$"),
]
NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class DomainModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class GeoPoint(DomainModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Lead(DomainModel):
    name: NonEmptyText
    address: str | None = None
    city: str | None = None
    state: str | None = None
    cep: NormalizedCep | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    website: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    reviews_count: int = Field(default=0, ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    distance_km: float | None = Field(default=None, ge=0)
    source: str | None = None
    source_id: str | None = None


class SearchRequest(DomainModel):
    cep: NormalizedCep
    category: NonEmptyText
    radius_km: float = Field(gt=0, le=50)


class SearchResult(DomainModel):
    origin_cep: NormalizedCep
    category: NonEmptyText
    radius_km: float = Field(gt=0, le=50)
    total_results: int = Field(ge=0)
    leads: list[Lead] = Field(default_factory=list)
