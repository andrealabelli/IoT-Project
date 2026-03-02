from app.auth.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_verify():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed)


def test_token_roundtrip():
    token = create_token("test@example.com", 5, "access")
    data = decode_token(token)
    assert data["sub"] == "test@example.com"
