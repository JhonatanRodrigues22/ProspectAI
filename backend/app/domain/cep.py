import re


class InvalidCepError(ValueError):
    """O CEP informado não possui um formato aceito."""


def normalize_cep(cep: str) -> str:
    if any(character.isalpha() for character in cep):
        raise InvalidCepError("CEP inválido. Informe exatamente 8 dígitos.")

    normalized_cep = re.sub(r"[^0-9]", "", cep)
    if len(normalized_cep) != 8:
        raise InvalidCepError("CEP inválido. Informe exatamente 8 dígitos.")

    return normalized_cep
