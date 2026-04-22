import json
import os
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.supabase_client import get_supabase
from ..services.diagnostic import enrich_company

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class IntakeForm(BaseModel):
    first_name: str
    last_name: str
    organization: str
    role: str
    email: str
    industry: Optional[str] = None


def _build_company_context(organization: str, role: str) -> dict:
    company_context = enrich_company(organization, role)
    if not company_context:
        company_context = {
            "known": False,
            "attempted_name": organization,
            "lookup_status": "no_match",
            "source": "model_plus_web_fallback",
        }
    return company_context


def _split_name(name: str) -> tuple[str, str]:
    normalized = (name or "").strip()
    if not normalized:
        return "", ""

    parts = normalized.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


@router.post("/")
async def create_session(form: IntakeForm):
    """Create a new public mode session. Silently enriches company context."""
    supabase = get_supabase()

    # Silently enrich company context
    company_context = _build_company_context(form.organization, form.role)

    # Use enriched industry if available
    industry = form.industry
    if company_context and company_context.get("industry"):
        industry = company_context.get("industry")

    result = supabase.table("sessions").insert({
        "mode": "public",
        "status": "intake",
        "first_name": form.first_name,
        "last_name": form.last_name,
        "organization": form.organization,
        "role": form.role,
        "email": form.email,
        "industry": industry,
        "referral_context": json.dumps({"company_enrichment": company_context}),
    }).execute()

    session = result.data[0]
    return {"session_id": session["id"], "mode": "public"}


@router.get("/referred")
async def create_referred_session(token: str = Query(...)):
    """Create a referred mode session from a signed referral token."""
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET is not configured")

    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="This link has expired or is invalid",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="This link has expired or is invalid",
        )

    name = payload.get("name")
    email = payload.get("email")
    organization = payload.get("organization")
    role = payload.get("role")
    context = payload.get("context")

    if not all([name, email, organization, role]):
        raise HTTPException(
            status_code=401,
            detail="This link has expired or is invalid",
        )

    first_name, last_name = _split_name(name)
    company_context = _build_company_context(organization, role)
    industry = company_context.get("industry")

    supabase = get_supabase()
    result = supabase.table("sessions").insert({
        "mode": "referred",
        "status": "intake",
        "first_name": first_name,
        "last_name": last_name,
        "organization": organization,
        "role": role,
        "email": email,
        "industry": industry,
        "referral_context": json.dumps({
            "context": context,
            "company_enrichment": company_context,
        }),
    }).execute()

    session = result.data[0]
    return {"session_id": session["id"], "mode": "referred"}