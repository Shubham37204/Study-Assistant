from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

from config import settings

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None


async def _fetch_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    if not settings.clerk_secret_key:
        return {"keys": []}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.clerk.com/v1/jwks",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


def _extract_key(token: str, jwks: dict):
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Malformed token")

    kid = header.get("kid")
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            return jwk.construct(key_data)

    raise HTTPException(status_code=401, detail="No matching signing key")


async def get_verified_user_id(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str | None:
    if not credentials:
        # Production fix: require credentials instead of returning None for user-scoped routes.
        return None

    token = credentials.credentials
    try:
        jwks = await _fetch_jwks()

        if not jwks.get("keys"):
            # Production fix: fail closed when Clerk auth is configured incorrectly.
            return None

        key = _extract_key(token, jwks)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            # Production fix: verify the expected Clerk audience/authorized party.
            options={"verify_aud": False},
        )
        return payload.get("sub")

    except HTTPException:
        raise
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Token invalid: {exc}")
    except Exception as exc:
        logger.exception("JWT verification failed")
        raise HTTPException(status_code=401, detail="Authentication failed")
    
