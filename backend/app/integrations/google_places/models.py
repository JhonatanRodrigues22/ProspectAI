from pydantic import BaseModel, ConfigDict, Field


def _to_camel(value: str) -> str:
    first, *remaining = value.split("_")
    return first + "".join(part.capitalize() for part in remaining)


class GoogleTextValue(BaseModel):
    text: str | None = None


class GoogleLocation(BaseModel):
    latitude: float | None = None
    longitude: float | None = None


class GoogleAddressComponent(BaseModel):
    long_text: str | None = None
    short_text: str | None = None
    types: list[str] = Field(default_factory=list)

    model_config = ConfigDict(alias_generator=_to_camel)


class GooglePlace(BaseModel):
    id: str | None = None
    display_name: GoogleTextValue | None = None
    formatted_address: str | None = None
    address_components: list[GoogleAddressComponent] = Field(
        default_factory=list
    )
    international_phone_number: str | None = None
    website_uri: str | None = None
    rating: float | None = None
    user_rating_count: int = 0
    location: GoogleLocation | None = None

    model_config = ConfigDict(alias_generator=_to_camel)


class GooglePlacesResponse(BaseModel):
    places: list[GooglePlace] = Field(default_factory=list)
