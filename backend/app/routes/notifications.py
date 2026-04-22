from fastapi import APIRouter
from ..services.resend_client import send_onboarding_email

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/resend-onboarding")
async def resend_onboarding():
    result = send_onboarding_email()
    return {"status": "sent", "provider": "resend", "result": result}
