from app.validators import (
    holder_matches_legal_name,
    validate_bic,
    validate_iban,
    validate_siren,
    validate_siret,
)


def test_siren_real_identifier_is_valid():
    assert validate_siren("913472056") is True


def test_siren_rejects_wrong_length():
    assert validate_siren("12345") is False


def test_siren_rejects_bad_checksum():
    assert validate_siren("913472057") is False


def test_siren_rejects_all_zeros_even_though_luhn_passes():
    assert validate_siren("000000000") is False


def test_siren_accepts_spaced_input():
    assert validate_siren("913 472 056") is True


def test_siren_none_is_invalid():
    assert validate_siren(None) is False


def test_siret_example_from_error_message_is_valid():
    # The SIRET shown in the field error ("913 472 056 00013") must itself be Luhn-valid,
    # so the example we tell users to follow actually passes.
    assert validate_siret("91347205600013") is True


def test_siret_rejects_bad_checksum():
    assert validate_siret("91347205600014") is False


def test_siret_rejects_wrong_length():
    assert validate_siret("12345") is False


def test_iban_real_identifier_is_valid():
    assert validate_iban("FR7618306000457021845630174") is True


def test_iban_accepts_spaced_input():
    assert validate_iban("FR76 1830 6000 4570 2184 5630 174") is True


def test_iban_rejects_tampered():
    assert validate_iban("FR7618306000457021845630175") is False


def test_iban_none_is_invalid():
    assert validate_iban(None) is False


def test_bic_real_identifier_is_valid():
    assert validate_bic("AGRIFRPP878") is True


def test_bic_eight_character_form_is_valid():
    assert validate_bic("AGRIFRPP") is True


def test_bic_rejects_bad_format():
    assert validate_bic("AGRI1234") is False


def test_cross_doc_holder_match_identical_names():
    assert (
        holder_matches_legal_name("SAVEURS DU SOLEIL LEVANT", "SAVEURS DU SOLEIL LEVANT")
        is True
    )


def test_cross_doc_holder_match_normalizes_whitespace():
    assert (
        holder_matches_legal_name("saveurs  du soleil levant ", "SAVEURS DU SOLEIL LEVANT")
        is True
    )


def test_cross_doc_holder_match_mismatch():
    assert holder_matches_legal_name("AUTRE SARL", "SAVEURS DU SOLEIL LEVANT") is False


def test_cross_doc_holder_match_missing_returns_none():
    assert holder_matches_legal_name(None, "SAVEURS DU SOLEIL LEVANT") is None
