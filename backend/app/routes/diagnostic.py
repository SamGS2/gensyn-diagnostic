import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.diagnostic import generate_next_question, generate_analysis, STAGES
from ..services.email import send_notification_email, send_results_email
from ..services.supabase_client import get_supabase

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])
logger = logging.getLogger(__name__)


class AnswerInput(BaseModel):
    session_id: str
    stage: int
    question_text: str
    response_type: str
    response_value: str
    options_presented: Optional[list] = None


class NextQuestionRequest(BaseModel):
    session_id: str


class AnalyzeRequest(BaseModel):
    session_id: str
    mode: str = "public"


@router.post("/next")
async def get_next_question(request: NextQuestionRequest):
    """Get the next diagnostic question based on previous answers."""
    supabase = get_supabase()

    # Get session info
    session_result = supabase.table("sessions") \
        .select("*") \
        .eq("id", request.session_id) \
        .execute()

    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_result.data[0]

    # Extract company context
    company_context = None
    if session.get("referral_context"):
        ref_context = session["referral_context"]
        if isinstance(ref_context, str):
            ref_context = json.loads(ref_context)
        company_context = ref_context.get("company_enrichment")

    # User info for personalization
    user_info = {
        "first_name": session.get("first_name", ""),
        "last_name": session.get("last_name", ""),
        "role": session.get("role", ""),
        "organization": session.get("organization", ""),
    }

    # Get existing responses
    result = supabase.table("diagnostic_responses") \
        .select("*") \
        .eq("session_id", request.session_id) \
        .order("stage") \
        .execute()

    previous_answers = []
    for row in result.data:
        previous_answers.append({
            "stage": row["stage"],
            "dimension": row.get("dimension", ""),
            "question_text": row["question_text"],
            "response_value": row["response_value"],
        })

    next_stage = len(previous_answers) + 1

    if next_stage > len(STAGES):
        return {"complete": True, "message": "Diagnostic complete."}

    if next_stage == 1:
        supabase.table("sessions") \
            .update({"status": "in_progress"}) \
            .eq("id", request.session_id) \
            .execute()

    question = generate_next_question(next_stage, previous_answers, company_context, user_info)

    return {"complete": False, "question": question}


@router.post("/answer")
async def submit_answer(answer: AnswerInput):
    """Submit an answer to a diagnostic question."""
    supabase = get_supabase()

    supabase.table("diagnostic_responses").insert({
        "session_id": answer.session_id,
        "stage": answer.stage,
        "question_text": answer.question_text,
        "response_type": answer.response_type,
        "response_value": answer.response_value,
        "options_presented": answer.options_presented,
    }).execute()

    return {"status": "saved", "stage": answer.stage}


@router.post("/analyze")
async def analyze_responses(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Generate the final analysis and recommendation."""
    supabase = get_supabase()

    # Get session
    session_result = supabase.table("sessions") \
        .select("*") \
        .eq("id", request.session_id) \
        .execute()

    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_result.data[0]

    # Company context
    company_context = None
    if session.get("referral_context"):
        ref_context = session["referral_context"]
        if isinstance(ref_context, str):
            ref_context = json.loads(ref_context)
        company_context = ref_context.get("company_enrichment")

    # User info
    user_info = {
        "first_name": session.get("first_name", ""),
        "last_name": session.get("last_name", ""),
        "role": session.get("role", ""),
        "organization": session.get("organization", ""),
    }

    # Get responses
    result = supabase.table("diagnostic_responses") \
        .select("*") \
        .eq("session_id", request.session_id) \
        .order("stage") \
        .execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="No responses found")

    responses = []
    for row in result.data:
        responses.append({
            "stage": row["stage"],
            "dimension": row.get("dimension", "unknown"),
            "question_text": row["question_text"],
            "response_value": row["response_value"],
        })

    analysis = generate_analysis(responses, request.mode, company_context, user_info)

    supabase.table("sessions").update({
        "status": "completed",
        "problem_classification": analysis.get("problem_type"),
        "workshop_recommendation": analysis.get("workshop_recommendation"),
        "analysis_text": json.dumps(analysis),
        "completed_at": "now()",
    }).eq("id", request.session_id).execute()

    full_name = f"{session.get('first_name', '')} {session.get('last_name', '')}".strip()
    if not full_name:
        full_name = session.get("first_name") or "there"

    try:
        background_tasks.add_task(
            send_results_email,
            session.get("email", ""),
            full_name,
            analysis,
            request.mode,
        )
    except Exception as exc:
        logger.exception("Failed to queue results email task: %s", exc)

    try:
        background_tasks.add_task(
            send_notification_email,
            session,
            analysis,
            responses,
        )
    except Exception as exc:
        logger.exception("Failed to queue notification email task: %s", exc)

    return analysis
    