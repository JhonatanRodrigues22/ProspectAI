import re

from backend.app.domain import Lead
from backend.app.integrations.google_places.models import (
    GoogleAddressComponent,
    GooglePlace,
)


class GooglePlaceMappingError(ValueError):
    """Um resultado do Google não possui os dados mínimos esperados."""


def map_google_place_to_lead(place: GooglePlace) -> Lead:
    name = place.display_name.text if place.display_name else None
    if not name:
        raise GooglePlaceMappingError(
            "O Google Places retornou um local sem nome."
        )

    return Lead(
        name=name,
        address=place.formatted_address,
        city=_component_value(place.address_components, "locality"),
        state=_component_value(
            place.address_components,
            "administrative_area_level_1",
            prefer_short=True,
        ),
        cep=_normalized_cep(place.address_components),
        phone=place.international_phone_number,
        website=place.website_uri,
        rating=place.rating,
        reviews_count=place.user_rating_count,
        latitude=place.location.latitude if place.location else None,
        longitude=place.location.longitude if place.location else None,
        source="google_places",
        source_id=place.id,
    )


def _component_value(
    components: list[GoogleAddressComponent],
    component_type: str,
    *,
    prefer_short: bool = False,
) -> str | None:
    for component in components:
        if component_type in component.types:
            if prefer_short:
                return component.short_text or component.long_text
            return component.long_text or component.short_text
    return None


def _normalized_cep(
    components: list[GoogleAddressComponent],
) -> str | None:
    postal_code = _component_value(components, "postal_code")
    if not postal_code:
        return None

    normalized = re.sub(r"[^0-9]", "", postal_code)
    return normalized if len(normalized) == 8 else None
