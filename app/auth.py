from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from .config import Settings, get_settings


def get_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token
    return None


def require_token(
    settings: Settings = Depends(get_settings),
    private_token: str | None = Header(default=None, alias="PRIVATE-TOKEN"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    expected = settings.mock_token
    provided = private_token or get_bearer_token(authorization)
    if provided != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
