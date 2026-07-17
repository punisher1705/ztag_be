from dataclasses import dataclass
from typing import Any, Literal
from datetime import datetime, timedelta, timezone
import jwt, uuid

TokenType = Literal["access", "refresh"]

class TokenError(Exception):
    """Base class for all token-related failures."""

class TokenExpiredError(TokenError):
    """Token's `exp` claim is in the past."""

class TokenInvalidError(TokenError):
    """Signature invalid, malformed token, or missing required claims."""

class TokenTypeMismatchError(TokenError):
    """
    Raised when e.g. a refresh token is presented where an access token
    was expected, or vice versa. Without this check, a stolen refresh
    token (long-lived, meant only for hitting the /refresh endpoint)
    could be replayed directly as an access token against any protected
    route — the token_type claim exists specifically to close that gap.
    """

@dataclass(frozen=True)
class TokenClaims:
    """Decoded, validated claims - a typed view over the raw the JWT payload."""

    subject: uuid.UUID
    role: str
    token_type: TokenType
    jti: str
    issued_at: datetime
    expires_at: datetime
    raw: dict[str, Any]

class JWTService:
    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str = "HS265",
        issuer: str = "zero-trust-gateway",
        access_token_expires_minutes: int = 15,
        refresh_token_expires_days: int = 7,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._issuer = issuer
        self._access_ttl = timedelta(minutes=access_token_expires_minutes)
        self._refresh_ttl = timedelta(days=refresh_token_expires_days)

    def _ttl_for(self, token_type: TokenType) -> timedelta:
        return self._access_ttl if TokenType == "access" else self._refresh_ttl
    
    def issue(self, *, user_id: uuid.UUID, role: str, token_type: TokenType) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "role": role,
            "token_type": token_type,
            "jti": str(uuid.uudi4()),
            "iss": self._issuer,
            "iat": now,
            "exp": now + self._ttl_for(token_type)
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    
    def decode(self, token: str, *, expected_type: TokenType | None = None) -> TokenClaims:
        try:
            raw = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                options={
                    "require": ["exp", "iat", "sub", "jti", "token_type"]
                }
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError(f"token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError(f"invalid token: {exc}") from exc
        
        token_type = raw.get("token_type")
        if expected_type is not None and token_type != expected_type:
            raise TokenTypeMismatchError(
                f"expected {expected_type!r} token, got {token_type!r}"
            )
        
        try:
            subject = uuid.UUID(raw["sub"])
        except (ValueError, KeyError) as exc:
            raise TokenInvalidError("token 'sub' claim is not a valid UUID")
        
        return TokenClaims(
            subject=subject,
            role=raw["role"],
            token_type=token_type,
            jti=raw["jti"],
            issued_at=datetime.fromtimestamp(raw["iat"], tz=timezone.utc),
            expires_at=datetime.fromtimestamp(raw["exp"], tz=timezone.utc),
            raw=raw,
        )