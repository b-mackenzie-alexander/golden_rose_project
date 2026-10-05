import base64
import json
import time
import urllib.error
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from golden_rose.auth.staff_oidc import (
    StaffAuthenticationFailedError,
    StaffIdentityProviderUnavailableError,
    StaffOidcJwksTokenVerifier,
    _fetch_jwks,
)
from golden_rose.config import Settings


def _settings() -> Settings:
    return Settings(
        environment="test",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer="https://accounts.example.test",
        staff_oidc_audience="golden-rose-staff",
        staff_oidc_jwks_url="https://accounts.example.test/.well-known/jwks.json",
    )


def _settings_with_issuer(issuer: str) -> Settings:
    return Settings(
        environment="test",
        auth_mode="staff_oidc",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=None,
        staff_oidc_issuer=issuer,
        staff_oidc_audience="golden-rose-staff",
        staff_oidc_jwks_url="https://accounts.example.test/.well-known/jwks.json",
    )


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _int_to_b64url(value: int) -> str:
    width = max(1, (value.bit_length() + 7) // 8)
    return _b64url(value.to_bytes(width, "big"))


class SigningKey:
    def __init__(self, *, key_id: str = "staff-key-1") -> None:
        self.key_id = key_id
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def jwk(self) -> dict[str, str]:
        numbers = self.private_key.public_key().public_numbers()
        return {
            "kty": "RSA",
            "kid": self.key_id,
            "alg": "RS256",
            "use": "sig",
            "n": _int_to_b64url(numbers.n),
            "e": _int_to_b64url(numbers.e),
        }

    def token(self, payload_updates: Mapping[str, Any] | None = None, *, key_id: str | None = None):
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT", "kid": key_id or self.key_id}
        payload: dict[str, Any] = {
            "iss": "https://accounts.example.test",
            "aud": "golden-rose-staff",
            "sub": "oidc:staff:123",
            "iat": now,
            "exp": now + 300,
            "amr": ["pwd", "mfa"],
            "sid": "session-123",
        }
        if payload_updates is not None:
            payload.update(payload_updates)
        signing_input = ".".join(
            (
                _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8")),
                _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
            )
        ).encode("ascii")
        signature = self.private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        return signing_input.decode("ascii") + "." + _b64url(signature)


def test_jwks_verifier_returns_staff_identity_claims() -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    claims = verifier.verify(token=key.token(), settings=_settings())

    assert claims.provider_subject == "oidc:staff:123"
    assert claims.mfa_verified is True
    assert claims.session_id == "session-123"


@pytest.mark.parametrize("token_issuer", ["accounts.google.com", "https://accounts.google.com"])
def test_jwks_verifier_accepts_google_issuer_aliases(token_issuer: str) -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    claims = verifier.verify(
        token=key.token({"iss": token_issuer}),
        settings=_settings_with_issuer("https://accounts.google.com"),
    )

    assert claims.provider_subject == "oidc:staff:123"


def test_jwks_verifier_keeps_non_google_issuer_matching_exact() -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    with pytest.raises(StaffAuthenticationFailedError):
        verifier.verify(
            token=key.token({"iss": "https://identity.example.test"}),
            settings=_settings_with_issuer("https://accounts.example.test"),
        )


def test_jwks_verifier_rejects_google_token_when_non_google_provider_configured() -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    with pytest.raises(StaffAuthenticationFailedError):
        verifier.verify(
            token=key.token({"iss": "accounts.google.com"}),
            settings=_settings_with_issuer("https://accounts.example.test"),
        )


def test_jwks_verifier_accepts_explicit_mfa_verified_claim() -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    claims = verifier.verify(
        token=key.token({"amr": ["pwd"], "mfa_verified": True, "sid": "", "jti": "jwt-123"}),
        settings=_settings(),
    )

    assert claims.mfa_verified is True
    assert claims.session_id == "jwt-123"


@pytest.mark.parametrize(
    "payload_update",
    [
        {"iss": "https://attacker.example.test"},
        {"aud": "wrong-audience"},
        {"sub": ""},
        {"exp": int(time.time()) - 120},
    ],
)
def test_jwks_verifier_rejects_invalid_core_claims(payload_update: Mapping[str, Any]) -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    with pytest.raises(StaffAuthenticationFailedError):
        verifier.verify(token=key.token(payload_update), settings=_settings())


def test_jwks_verifier_preserves_missing_mfa_as_unverified_claim() -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    claims = verifier.verify(token=key.token({"amr": ["pwd"]}), settings=_settings())

    assert claims.mfa_verified is False


def test_jwks_verifier_rejects_unknown_key_id() -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    with pytest.raises(StaffAuthenticationFailedError):
        verifier.verify(token=key.token(key_id="missing-key"), settings=_settings())


@pytest.mark.parametrize(
    "jwks",
    [
        {},
        {"keys": []},
        {"keys": [{"kty": "oct", "kid": "secret"}]},
        {"keys": [{"kty": "RSA", "kid": "staff-key-1", "alg": "HS256", "n": "aa", "e": "AQAB"}]},
    ],
)
def test_jwks_verifier_rejects_malformed_or_unusable_jwks(jwks: Mapping[str, Any]) -> None:
    key = SigningKey()
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: jwks)

    with pytest.raises(StaffAuthenticationFailedError):
        verifier.verify(token=key.token(), settings=_settings())


def test_jwks_verifier_fails_closed_when_provider_fetch_fails() -> None:
    key = SigningKey()

    def fail_fetch(_url: str) -> Mapping[str, Any]:
        raise StaffIdentityProviderUnavailableError("provider unavailable")

    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=fail_fetch)

    with pytest.raises(StaffIdentityProviderUnavailableError):
        verifier.verify(token=key.token(), settings=_settings())


def test_jwks_verifier_maps_network_fetch_failure_to_provider_unavailable() -> None:
    key = SigningKey()

    def fail_fetch(_url: str) -> Mapping[str, Any]:
        raise urllib.error.URLError("network unavailable")

    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=fail_fetch)

    with pytest.raises(StaffIdentityProviderUnavailableError):
        verifier.verify(token=key.token(), settings=_settings())


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://accounts.example.test/.well-known/jwks.json",
        "https://",
        "https://accounts.example.test/.well-known/jwks.json\n",
    ],
)
def test_jwks_fetch_rejects_unsafe_url_before_network(
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    def fail_urlopen(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("unsafe jwks url reached urlopen")

    monkeypatch.setattr("golden_rose.auth.staff_oidc.urllib.request.urlopen", fail_urlopen)

    with pytest.raises(StaffIdentityProviderUnavailableError, match="jwks url is invalid"):
        _fetch_jwks(url)


def test_jwks_verifier_requires_staff_oidc_mode() -> None:
    key = SigningKey()
    settings = Settings(
        environment="local",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
    )
    verifier = StaffOidcJwksTokenVerifier(fetch_jwks=lambda _url: {"keys": [key.jwk()]})

    with pytest.raises(StaffAuthenticationFailedError):
        verifier.verify(token=key.token(), settings=settings)


def test_jwks_verifier_public_key_pem_is_serializable() -> None:
    key = SigningKey()

    pem = key.private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    assert pem.startswith(b"-----BEGIN PUBLIC KEY-----")
