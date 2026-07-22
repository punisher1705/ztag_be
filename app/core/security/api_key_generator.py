"""
API key generation.
 
Uses `secrets`, not `random` — `random` is a Mersenne Twister PRNG,
predictable given enough output, and never appropriate for anything
security-sensitive. `secrets` is specifically the stdlib module for
generating tokens, passwords, and keys.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

KEY_PREFIX = "gwk"
KEY_ID = 9
SECRET_BYTES = 32

@dataclass(frozen=True)
class GeneratedApiKey:
    """
    Result of generating a new key.
 
    `full_key` is shown to the caller exactly once, at creation time,
    and never stored anywhere. `key_id` and `hashed_secret` are what
    actually get persisted to the `ApiKey` row.
    """
 
    key_id: str
    secret: str
    full_key: str

def parse_api_key(raw: str) -> tuple[str, str]:
    """
    Split a presented key back into (key_id, secret).
 
    Raises ValueError on any malformed input — missing prefix, missing
    separator, empty parts — so the caller (the auth strategy) can
    treat any parse failure as "invalid credential" uniformly.
    """
    if not raw.startswith(f"{KEY_PREFIX}_"):
        return ValueError(f"API key must start with '{KEY_PREFIX}_'")
    
    remainder = raw[len(KEY_PREFIX) + 1 :]
    if "." not in remainder:
        raise ValueError("malformed API key: missing key_id/secret separator")
    
    key_id, _, secret = remainder.partition(".")
    if not key_id or not secret:
        raise ValueError("malformed API key: empty key_id or secret")
    
    return key_id, secret
