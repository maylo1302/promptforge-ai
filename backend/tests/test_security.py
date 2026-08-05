from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_is_hashed_and_verified() -> None:
    password_hash = hash_password("bardzo-dlugie-i-bezpieczne-haslo")
    assert password_hash != "bardzo-dlugie-i-bezpieczne-haslo"
    assert verify_password("bardzo-dlugie-i-bezpieczne-haslo", password_hash)
    assert not verify_password("błędne-hasło", password_hash)


def test_access_token_has_expected_subject() -> None:
    token = create_access_token("user-123", False)
    assert decode_access_token(token)["sub"] == "user-123"

