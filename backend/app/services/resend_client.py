import os
import requests
from fastapi import HTTPException


RESEND_API_URL = "https://api.resend.com/emails"


def send_onboarding_email() -> dict:
    api_key = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("RESEND_TO_EMAIL")
    from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    if not api_key:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY is not configured.")
    if not to_email:
        raise HTTPException(status_code=500, detail="RESEND_TO_EMAIL is not configured.")

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Hello World",
        "html": "<p>Congrats on sending your <strong>first email</strong>!</p>",
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(RESEND_API_URL, json=payload, headers=headers, timeout=20)
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Resend API error ({response.status_code}): {response.text}",
        )

    return response.json()
