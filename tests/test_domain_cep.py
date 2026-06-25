import pytest

from backend.app.domain import InvalidCepError, normalize_cep


@pytest.mark.parametrize(
    ("raw_cep", "expected"),
    [
        ("12900000", "12900000"),
        ("12900-000", "12900000"),
        ("12.900-000", "12900000"),
    ],
)
def test_normalize_cep(raw_cep: str, expected: str) -> None:
    assert normalize_cep(raw_cep) == expected


@pytest.mark.parametrize("cep", ["123", "12900A000"])
def test_normalize_cep_rejects_invalid_value(cep: str) -> None:
    with pytest.raises(InvalidCepError):
        normalize_cep(cep)
