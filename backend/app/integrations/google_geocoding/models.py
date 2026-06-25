from pydantic import BaseModel, Field


class GoogleGeocodingLocation(BaseModel):
    lat: float
    lng: float


class GoogleGeocodingGeometry(BaseModel):
    location: GoogleGeocodingLocation


class GoogleGeocodingResult(BaseModel):
    geometry: GoogleGeocodingGeometry


class GoogleGeocodingResponse(BaseModel):
    status: str
    results: list[GoogleGeocodingResult] = Field(default_factory=list)
    error_message: str | None = None
