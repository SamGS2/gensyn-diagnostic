import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


class GenerateLinkRequest(BaseModel):
    name: str
    email: str
    organization: str
    role: str
    context: Optional[str] = None


@router.post("/generate-link")
async def generate_link(
    payload: GenerateLinkRequest,
    authorization: Optional[str] = Header(default=None),
):
    admin_api_key = os.getenv("ADMIN_API_KEY")
    jwt_secret = os.getenv("JWT_SECRET")

    if not admin_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.split(" ", 1)[1].strip()
    if token != admin_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not jwt_secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET is not configured")

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(days=30)

    jwt_payload = {
        "name": payload.name,
        "email": payload.email,
        "organization": payload.organization,
        "role": payload.role,
        "context": payload.context,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    signed_token = jwt.encode(jwt_payload, jwt_secret, algorithm="HS256")
    url = f"https://diagnostic.gensyn.co/referred?token={signed_token}"
    return {"url": url}
