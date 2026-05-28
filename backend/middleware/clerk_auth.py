# backend/middleware/clerk_auth.py
import os
import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None

async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    clerk_secret = os.getenv("CLERK_SECRET_KEY")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.clerk.com/v1/jwks",
            headers={"Authorization": f"Bearer {clerk_secret}"},
        )
        r.raise_for_status()
        _jwks_cache = r.json()
        return _jwks_cache


async def get_verified_user_id(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str | None:
    # if no token present, return None — routes decide if auth is required
    if not credentials:
        return None

    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")