import re

_IBAN_COUNTRY_LENGTHS = {"FR": 27}
_BIC_PATTERN = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value)


def _luhn_valid(digits: str) -> bool:
    total = 0
    reverse = digits[::-1]
    for index, character in enumerate(reverse):
        digit = int(character)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def validate_siren(value: str | None) -> bool:
    if value is None:
        return False
    digits = _digits_only(value)
    if len(digits) != 9 or set(digits) == {"0"}:
        return False
    return _luhn_valid(digits)


def validate_siret(value: str | None) -> bool:
    if value is None:
        return False
    digits = _digits_only(value)
    if len(digits) != 14 or set(digits) == {"0"}:
        return False
    return _luhn_valid(digits)


def validate_iban(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    if len(cleaned) < 4 or not cleaned[:2].isalpha() or not cleaned[2:4].isdigit():
        return False
    expected_length = _IBAN_COUNTRY_LENGTHS.get(cleaned[:2])
    if expected_length is not None and len(cleaned) != expected_length:
        return False
    rearranged = cleaned[4:] + cleaned[:4]
    numeric = "".join(
        str(int(character, 36)) if character.isalnum() else "" for character in rearranged
    )
    if not numeric.isdigit():
        return False
    return int(numeric) % 97 == 1


def validate_bic(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    return bool(_BIC_PATTERN.match(cleaned))


def normalize_company_name(value: str | None) -> str:
    if value is None:
        return ""
    collapsed = re.sub(r"\s+", " ", value.strip().upper())
    return collapsed


def holder_matches_legal_name(holder: str | None, legal_name: str | None) -> bool | None:
    if not holder or not legal_name:
        return None
    return normalize_company_name(holder) == normalize_company_name(legal_name)
