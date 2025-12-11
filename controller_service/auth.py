from fastapi import Header, HTTPException, Depends
from typing import Optional
from jose import jwt, JWTError

SECRET = "dev-secret-change-me"
ALGORITHM = "HS256"


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_roles(authorization: Optional[str] = Header(None)) -> list:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    raw = authorization.split(" ", 1)[1]
    payload = decode_token(raw)
    roles = payload.get("roles", [])
    if not isinstance(roles, list):
        roles = [roles]
    return roles


def require_roles(roles_needed: list):
    async def checker(user_roles: list = Depends(get_current_roles)):
        if not any(r in user_roles for r in roles_needed):
            raise HTTPException(status_code=403, detail="Forbidden")
    return checker
