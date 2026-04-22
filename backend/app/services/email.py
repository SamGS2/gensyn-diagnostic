import html
import logging
import os
from typing import Any

import resend

logger = logging.getLogger(__name__)
resend.api_key = os.getenv("RESEND_API_KEY")


def _safe(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    return html.escape(text)


def _analysis_paragraphs(analysis_text: str) -> str:
    chunks = [part.strip() for part in (analysis_text or "").split("\n") if part.strip()]
    if not chunks:
        return '<p style="margin: 0 0 12px; color: #1f2937; line-height: 1.6;">No additional analysis provided.</p>'

    return "".join(
        f'<p style="margin: 0 0 12px; color: #1f2937; line-height: 1.6;">{_safe(paragraph)}</p>'
        for paragraph in chunks
    )


def _next_steps_list(steps: Any) -> str:
    if not isinstance(steps, list) or not steps:
        return '<p style="margin: 0; color: #1f2937; line-height: 1.6;">No specific next steps were provided.</p>'

    items = "".join(
        f'<li style="margin: 0 0 8px;">{_safe(step)}</li>'
        for step in steps
    )
    return f'<ul style="margin: 0; padding-left: 20px; color: #1f2937; line-height: 1.6;">{items}</ul>'


def send_results_email(user_email: str, user_name: str, analysis_data: dict, mode: str) -> None:
    """Send user-facing diagnostic results email via Resend."""
    try:
        resend.api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

        if not resend.api_key:
            logger.error("send_results_email skipped: RESEND_API_KEY is not configured.")
            return
        if not user_email:
            logger.error("send_results_email skipped: user_email is missing.")
            return

        problem_summary = _safe(analysis_data.get("problem_summary"), "No summary available.")
        problem_type = _safe(analysis_data.get("problem_type"), "Unknown")
        problem_type_explanation = _safe(
            analysis_data.get("problem_type_explanation"),
            "No explanation available.",
        )
        analysis_html = _analysis_paragraphs(analysis_data.get("analysis", ""))
        recommendation = _safe(analysis_data.get("workshop_recommendation"), "")
        recommendation_explanation = _safe(analysis_data.get("recommendation_explanation"), "")
        next_steps_html = _next_steps_list(analysis_data.get("suggested_next_steps"))

        recommendation_block = ""
        if mode == "public" and recommendation:
            recommendation_block = f"""
              <div style="margin: 0 0 24px;">
                <h3 style="margin: 0 0 10px; color: #263171; font-size: 18px;">Recommended Workshop</h3>
                <p style="margin: 0 0 8px; color: #743694; font-weight: 700;">{recommendation}</p>
                <p style="margin: 0; color: #1f2937; line-height: 1.6;">{recommendation_explanation or "No recommendation details available."}</p>
              </div>
            """

        email_html = f"""
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Your Diagnostic Results</title>
          </head>
          <body style="margin: 0; padding: 0; background-color: #ffffff; font-family: Arial, Helvetica, sans-serif;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #ffffff;">
              <tr>
                <td align="center" style="padding: 24px 12px;">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
                    <tr>
                      <td style="background: #263171; color: #ffffff; padding: 20px 24px;">
                        <h1 style="margin: 0; font-size: 22px; line-height: 1.2;">Gensyn Diagnostic Results</h1>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding: 24px;">
                        <p style="margin: 0 0 20px; color: #1f2937; line-height: 1.6;">
                          Hi {_safe(user_name, "there")},
                        </p>

                        <div style="margin: 0 0 24px;">
                          <h3 style="margin: 0 0 10px; color: #263171; font-size: 18px;">Problem Summary</h3>
                          <p style="margin: 0; color: #1f2937; line-height: 1.6;">{problem_summary}</p>
                        </div>

                        <div style="margin: 0 0 24px;">
                          <h3 style="margin: 0 0 10px; color: #263171; font-size: 18px;">Problem Type</h3>
                          <p style="margin: 0 0 8px; color: #743694; font-weight: 700; text-transform: capitalize;">{problem_type}</p>
                          <p style="margin: 0; color: #1f2937; line-height: 1.6;">{problem_type_explanation}</p>
                        </div>

                        <div style="margin: 0 0 24px;">
                          <h3 style="margin: 0 0 10px; color: #263171; font-size: 18px;">Analysis</h3>
                          {analysis_html}
                        </div>

                        {recommendation_block}

                        <div style="margin: 0 0 28px;">
                          <h3 style="margin: 0 0 10px; color: #263171; font-size: 18px;">Suggested Next Steps</h3>
                          {next_steps_html}
                        </div>

                        <table role="presentation" cellspacing="0" cellpadding="0">
                          <tr>
                            <td style="border-radius: 8px; background: #743694;">
                              <a
                                href="https://www.gensyndesign.com"
                                style="display: inline-block; padding: 12px 18px; font-size: 14px; color: #ffffff; text-decoration: none; font-weight: 700;"
                              >
                                Explore Gensyn Design
                              </a>
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """

        resend.Emails.send({
            "from": from_email,
            "to": [user_email],
            "subject": "Your Diagnostic Results — Gensyn \\Design",
            "html": email_html,
        })
    except Exception as exc:
        logger.exception("Failed to send results email: %s", exc)


def send_notification_email(session_data: dict, analysis_data: dict, responses: list) -> None:
    """Send internal completion notification email with full diagnostic details."""
    try:
        resend.api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        notification_email = os.getenv("NOTIFICATION_EMAIL")

        if not resend.api_key:
            logger.error("send_notification_email skipped: RESEND_API_KEY is not configured.")
            return
        if not notification_email:
            logger.error("send_notification_email skipped: NOTIFICATION_EMAIL is not configured.")
            return

        first_name = (session_data.get("first_name") or "").strip()
        last_name = (session_data.get("last_name") or "").strip()
        user_name = f"{first_name} {last_name}".strip() or "Unknown User"
        organization = _safe(session_data.get("organization"), "Unknown Organization")
        mode = _safe(session_data.get("mode"), "unknown")
        role = _safe(session_data.get("role"), "Unknown Role")
        user_email = _safe(session_data.get("email"), "Unknown Email")

        response_rows = []
        for item in responses or []:
            stage = _safe(item.get("stage"), "?")
            question = _safe(item.get("question_text"), "(missing question)")
            answer = _safe(item.get("response_value"), "(missing answer)")
            response_rows.append(
                f"<li style='margin: 0 0 12px;'>"
                f"<strong>Stage {stage}</strong><br>"
                f"Q: {question}<br>"
                f"A: {answer}"
                f"</li>"
            )
        response_html = (
            "<ol style='margin: 0; padding-left: 20px; line-height: 1.5;'>"
            + "".join(response_rows)
            + "</ol>"
        ) if response_rows else "<p>No responses captured.</p>"

        recommendation_block = ""
        if mode == "public":
            recommendation_block = (
                f"<p><strong>Workshop recommendation:</strong> {_safe(analysis_data.get('workshop_recommendation'), 'None')}</p>"
                f"<p><strong>Recommendation explanation:</strong> {_safe(analysis_data.get('recommendation_explanation'), 'None')}</p>"
            )

        internal_html = f"""
        <div style="font-family: Arial, Helvetica, sans-serif; color: #111827; line-height: 1.5;">
          <h2 style="margin-bottom: 10px;">New Diagnostic Completed</h2>
          <p><strong>Name:</strong> {_safe(user_name)}</p>
          <p><strong>Email:</strong> {user_email}</p>
          <p><strong>Organization:</strong> {organization}</p>
          <p><strong>Role:</strong> {role}</p>
          <p><strong>Mode:</strong> {mode}</p>
          <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 18px 0;" />
          <p><strong>Problem summary:</strong> {_safe(analysis_data.get("problem_summary"), "No summary available.")}</p>
          <p><strong>Problem type:</strong> {_safe(analysis_data.get("problem_type"), "Unknown")}</p>
          <p><strong>Problem type explanation:</strong> {_safe(analysis_data.get("problem_type_explanation"), "No explanation available.")}</p>
          {recommendation_block}
          <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 18px 0;" />
          <h3 style="margin: 0 0 10px;">Diagnostic Responses</h3>
          {response_html}
        </div>
        """

        resend.Emails.send({
            "from": from_email,
            "to": [notification_email],
            "subject": f"New Diagnostic Completed — {_safe(user_name)} at {organization}",
            "html": internal_html,
        })
    except Exception as exc:
        logger.exception("Failed to send notification email: %s", exc)
