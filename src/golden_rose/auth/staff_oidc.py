import base64
import binascii
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any, Protocol, cast

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from google.auth import exceptions as google_auth_exceptions
from google.auth import jwt

from golden_rose.auth.staff_accounts import StaffIdentityClaims
from golden_rose.config import Settings

JwksFetcher = Callable[[str], Mapping[str, Any]]
MFA_AUTHENTICATION_METHODS = frozenset({"mfa"})
GOOGLE_OIDC_ISSUERS = frozenset({"https://accounts.google.com", "accounts.google.com"})


class StaffAuthenticationError(RuntimeError):
    pass


class StaffAuthenticationRequiredError(StaffAuthenticationError):
    pass


class StaffAuthenticationFailedError(StaffAuthenticationError):
    pass


class StaffIdentityProviderUnavailableError(StaffAuthenticationError):
    pass


class StaffAccountUnavailableError(PermissionError):
    pass


class StaffOidcTokenVerifier(Protocol):
    def verify(self, *, token: str, settings: Settings) -> StaffIdentityClaims:
        raise NotImplementedError


class StaffOidcJwksTokenVerifier:
    def __init__(self, fetch_jwks: JwksFetcher | None = None) -> None:
        self._fetch_jwks = fetch_jwks or _fetch_jwks

    def verify(self, *, token: str, settings: Settings) -> StaffIdentityClaims:
        if settings.auth_mode != "staff_oidc":
            raise StaffAuthenticationFailedError("staff oidc auth is not enabled")
        _require_staff_oidc_settings(settings)
        try:
            header = cast("Mapping[str, Any]", cast(Any, jwt.decode_header)(token))
        except (ValueError, google_auth_exceptions.GoogleAuthError) as exc:
            raise StaffAuthenticationFailedError("staff identity token is invalid") from exc
        if header.get("alg") != "RS256":
            raise StaffAuthenticationFailedError("staff identity token algorithm is unsupported")

        try:
            certs = _jwks_to_certs(self._fetch_jwks(settings.staff_oidc_jwks_url or ""))
            payload = cast(
                "Mapping[str, Any]",
                cast(Any, jwt.decode)(
                    token,
                    certs=certs,
                    audience=settings.staff_oidc_audience,
                    clock_skew_in_seconds=60,
                ),
            )
        except (StaffIdentityProviderUnavailableError, urllib.error.URLError) as exc:
            raise StaffIdentityProviderUnavailableError(
                "staff identity provider jwks unavailable"
            ) from exc
        except StaffAuthenticationFailedError:
            raise
        except (
            KeyError,
            TypeError,
            ValueError,
            google_auth_exceptions.GoogleAuthError,
        ) as exc:
            raise StaffAuthenticationFailedError("staff identity token is invalid") from exc

        if not _issuer_matches_configured_provider(
            payload.get("iss"),
            settings.staff_oidc_issuer,
        ):
            raise StaffAuthenticationFailedError("staff identity token issuer is invalid")
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise StaffAuthenticationFailedError("staff identity token subject is invalid")
        return StaffIdentityClaims(
            provider_subject=subject.strip(),
            mfa_verified=_has_mfa_claim(payload),
            session_id=_optional_string_claim(payload, "sid")
            or _optional_string_claim(payload, "jti"),
        )


def _require_staff_oidc_settings(settings: Settings) -> None:
    if not settings.staff_oidc_issuer or not settings.staff_oidc_audience:
        raise StaffIdentityProviderUnavailableError("staff oidc settings are incomplete")
    if not settings.staff_oidc_jwks_url:
        raise StaffIdentityProviderUnavailableError("staff oidc jwks url is not configured")


def _issuer_matches_configured_provider(
    token_issuer: object,
    configured_issuer: str | None,
) -> bool:
    if not isinstance(token_issuer, str) or configured_issuer is None:
        return False
    if configured_issuer in GOOGLE_OIDC_ISSUERS:
        return token_issuer in GOOGLE_OIDC_ISSUERS
    return token_issuer == configured_issuer


def _fetch_jwks(url: str) -> Mapping[str, Any]:
    url = _require_https_url(url)
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    # The URL is restricted to HTTPS above; Bandit cannot infer that guard.
    with urllib.request.urlopen(request, timeout=5) as response:  # nosec B310
        if response.status != 200:
            raise StaffIdentityProviderUnavailableError("staff identity provider jwks unavailable")
        body = response.read(262_144)
    parsed = json.loads(body.decode("utf-8"))
    if not isinstance(parsed, Mapping):
        raise StaffAuthenticationFailedError("staff identity provider jwks is invalid")
    return parsed


def _require_https_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise StaffIdentityProviderUnavailableError("staff identity provider jwks url is invalid")
    if any(ch.isspace() for ch in url):
        raise StaffIdentityProviderUnavailableError("staff identity provider jwks url is invalid")
    return url


def _jwks_to_certs(jwks: Mapping[str, Any]) -> dict[str, str]:
    keys = jwks.get("keys")
    if not isinstance(keys, list) or not keys:
        raise StaffAuthenticationFailedError("staff identity provider jwks is invalid")
    certs: dict[str, str] = {}
    for key in keys:
        if not isinstance(key, Mapping):
            continue
        converted = _rsa_jwk_to_pem(key)
        if converted is not None:
            key_id, pem = converted
            certs[key_id] = pem
    if not certs:
        raise StaffAuthenticationFailedError("staff identity provider jwks has no usable keys")
    return certs


def _rsa_jwk_to_pem(key: Mapping[str, Any]) -> tuple[str, str] | None:
    key_id = key.get("kid")
    modulus = key.get("n")
    exponent = key.get("e")
    if key.get("kty") != "RSA" or not isinstance(key_id, str):
        return None
    if key.get("alg") not in (None, "RS256"):
        return None
    if not isinstance(modulus, str) or not isinstance(exponent, str):
        return None
    public_numbers = rsa.RSAPublicNumbers(
        e=_base64url_uint(exponent),
        n=_base64url_uint(modulus),
    )
    public_key = public_numbers.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return key_id, pem


def _base64url_uint(value: str) -> int:
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (binascii.Error, ValueError) as exc:
        raise StaffAuthenticationFailedError("staff identity provider jwks is invalid") from exc
    if not decoded:
        raise StaffAuthenticationFailedError("staff identity provider jwks is invalid")
    return int.from_bytes(decoded, "big")


def _has_mfa_claim(payload: Mapping[str, Any]) -> bool:
    if payload.get("mfa_verified") is True:
        return True
    methods = payload.get("amr")
    return isinstance(methods, list) and any(
        isinstance(item, str) and item in MFA_AUTHENTICATION_METHODS for item in methods
    )


def _optional_string_claim(payload: Mapping[str, Any], name: str) -> str | None:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()
