import anthropic
import json
import os
import re
from urllib import parse, request

HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-6"

from .rag import build_framework_context

def get_anthropic_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip()


def _normalized_company_variants(company_name: str) -> list[str]:
    base = (company_name or "").strip()
    if not base:
        return []

    variants = [base]
    simplified = re.sub(r"[^\w\s&.-]", "", base).strip()
    if simplified and simplified not in variants:
        variants.append(simplified)

    no_suffix = re.sub(
        r"\b(inc|inc\.|llc|l\.l\.c\.|ltd|ltd\.|corp|corp\.|corporation|co|co\.|company|plc|gmbh)\b",
        "",
        simplified,
        flags=re.IGNORECASE,
    )
    no_suffix = re.sub(r"\s+", " ", no_suffix).strip(" ,.-")
    if no_suffix and no_suffix not in variants:
        variants.append(no_suffix)

    return variants


def _infer_size_from_excerpt(excerpt: str) -> str:
    text = (excerpt or "").lower()
    if any(k in text for k in ["fortune 500", "global", "multinational", "public company"]):
        return "enterprise"
    if any(k in text for k in ["regional", "multiple locations", "nationwide"]):
        return "large"
    if any(k in text for k in ["family-owned", "local business", "small business"]):
        return "small"
    return "medium"


def _lookup_company_api(company_name: str, role: str, client) -> dict | None:
    """Fallback company lookup via SerpAPI Google results + Haiku extraction.
    Requires SERPAPI_KEY in environment."""
    serp_key = os.getenv("SERPAPI_KEY")
    if not serp_key:
        return None

    base = (company_name or "").strip()
    if not base:
        return None

    search_queries = [
        f"\"{base}\" Fort Wayne Indiana manufacturer",
        f"\"{base}\" Indiana company",
        base,
    ]

    for q in search_queries:
        try:
            params = parse.urlencode(
                {
                    "engine": "google",
                    "q": q,
                    "num": 5,
                    "api_key": serp_key,
                }
            )
            search_url = f"https://serpapi.com/search.json?{params}"
            with request.urlopen(search_url, timeout=3) as resp:
                payload = json.loads(resp.read().decode("utf-8"))

            organic = payload.get("organic_results", []) if isinstance(payload, dict) else []
            if not organic:
                continue

            snippets = []
            for item in organic[:5]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                snippets.append(f"- Title: {title}\n  Snippet: {snippet}\n  URL: {link}")

            extraction_prompt = f"""Determine whether these search results refer to the company "{base}" (role: "{role}").
Prioritize NE Indiana / Indiana interpretation when multiple matches exist.
If confident, return JSON:
{{"known": true, "industry": "...", "description": "...", "approximate_size": "startup/small/medium/large/enterprise", "sector": "private/public/nonprofit/government", "matched_name": "...", "matched_url": "..."}}
If not confident, return JSON:
{{"known": false}}

Search results:
{chr(10).join(snippets)}

Return ONLY valid JSON."""

            message = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=220,
                messages=[{"role": "user", "content": extraction_prompt}],
            )
            parsed = json.loads(_strip_code_fences(message.content[0].text))
            if parsed.get("known"):
                parsed["source"] = "serpapi"
                parsed["confidence"] = "medium"
                return parsed
        except Exception:
            continue

    return None


def enrich_company(company_name: str, role: str) -> dict | None:
    """Silently enrich company context using Haiku's training data.
    Returns company info dict or None if unknown.
    Biased toward US companies when ambiguous."""
    client = get_anthropic_client()
    variants = _normalized_company_variants(company_name)

    for variant in variants:
        try:
            message = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=180,
                messages=[{
                    "role": "user",
                    "content": f"""What do you know about the company "{variant}"?
The user role is "{role}".
When ambiguous, prefer local matches in this order:
1) Northeast Indiana companies (e.g. Fort Wayne metro and nearby counties)
2) Indiana companies
3) US-based companies
4) Non-US companies
If there are multiple possible matches, choose the one in the highest-priority geography above.
If you are reasonably confident you know this company, respond with JSON:
{{"known": true, "industry": "their industry", "description": "one sentence what they do", "approximate_size": "startup/small/medium/large/enterprise", "sector": "private/public/nonprofit/government"}}

If you don't recognize this company or aren't confident, respond with:
{{"known": false}}

ONLY valid JSON, nothing else."""
                }]
            )
            response_text = _strip_code_fences(message.content[0].text)
            result = json.loads(response_text)
            if result.get("known"):
                return result
        except Exception:
            continue

    # Fallback to API-based web lookup when model knowledge is missing.
    api_result = _lookup_company_api(company_name, role, client)
    if api_result:
        return api_result

    return None


def clean_name(name: str) -> str:
    """Clean up a name - fix obvious typos, capitalization."""
    if not name:
        return name
    # Basic capitalization fix
    name = name.strip()
    if name.islower() or name.isupper():
        name = name.title()
    return name


STAGES = [
    {
        "stage": 1,
        "dimension": "role_and_context",
        "description": "Understand the person's role, responsibilities, and what they're trying to achieve.",
        "prompt": """You are a diagnostic tool helping a team leader articulate a business problem.
You are at Stage 1: Role & Context.

{company_context}

Address the user by their first name: {first_name}.
Ask ONE warm, open-ended question that helps you understand:
- What they're responsible for in their role
- What they're currently focused on or trying to achieve
Make it feel like the start of a real conversation, not a form.
If you have company context, reference it naturally (e.g. "At [company], as a [role]...").

Respond ONLY with valid JSON:
{{"question_text": "your question", "response_type": "short_text", "options": null}}"""
    },
    {
        "stage": 2,
        "dimension": "problem_identification",
        "description": "What is the core issue or challenge?",
        "prompt": """You are a diagnostic tool helping a team leader articulate a business problem.
You are at Stage 2: Problem Identification.

{company_context}

Address the user as {first_name}.
Based on what they've shared about their role, ask ONE clear question that helps them describe the specific challenge or issue they're facing.
Keep it open-ended — give them space to write. Don't suggest answers.

Respond ONLY with valid JSON:
{{"question_text": "your question", "response_type": "short_text", "options": null}}"""
    },
    {
        "stage": 3,
        "dimension": "problem_depth",
        "description": "Dig deeper — context, history, who's affected.",
        "prompt": """You are a diagnostic tool helping a team leader articulate a business problem.
You are at Stage 3: Problem Depth.

{company_context}

Based on what {first_name} has shared, ask ONE follow-up that digs deeper.
How long has this been going on? What triggered it? Who is affected?
Choose the best format:
- "short_text" if their previous answer was brief and needs elaboration
- "selection" with 4 options if you can anticipate likely answers

Respond ONLY with valid JSON:
{{"question_text": "your question", "response_type": "short_text or selection", "options": null or ["opt1", "opt2", "opt3", "opt4"]}}"""
    },
    {
        "stage": 4,
        "dimension": "scope_and_impact",
        "description": "How broad is this and what's at stake?",
        "prompt": """You are a diagnostic tool helping a team leader articulate a business problem.
You are at Stage 4: Scope & Impact.

{company_context}

Based on what {first_name} has shared, ask ONE question about scope.
Is this one team, cross-functional, or org-wide? What's at stake?
Use "selection" with 4 options that feel specific to their situation.

Respond ONLY with valid JSON:
{{"question_text": "your question", "response_type": "selection", "options": ["opt1", "opt2", "opt3", "opt4"]}}"""
    },
    {
        "stage": 5,
        "dimension": "solution_readiness",
        "description": "THE KEY SIGNAL: Has the team identified solutions or not?",
        "prompt": """You are a diagnostic tool helping a team leader articulate a business problem.
You are at Stage 5: Current State of Thinking. THIS IS THE MOST IMPORTANT STAGE.

{company_context}

Based on what {first_name} has shared, ask ONE question that reveals whether:
(a) The team has potential solutions but can't agree, OR
(b) No clear solutions or next steps exist at all.

This distinction determines the final recommendation. Use "selection" with 4 options that clearly separate "we have ideas but can't align" from "we don't know where to start."
Make the options specific to their situation, not generic.

Respond ONLY with valid JSON:
{{"question_text": "your question", "response_type": "selection", "options": ["opt1", "opt2", "opt3", "opt4"]}}"""
    },
    {
        "stage": 6,
        "dimension": "team_dynamics",
        "description": "Team alignment, stakeholders, decision-making.",
        "prompt": """You are a diagnostic tool helping a team leader articulate a business problem.
You are at Stage 6: Team Dynamics.

{company_context}

Based on what {first_name} has shared, ask ONE question about how the team is functioning around this issue.
Stakeholder alignment, decision-making, engagement level.
Choose the best format based on context.

Respond ONLY with valid JSON:
{{"question_text": "your question", "response_type": "short_text or selection", "options": null or ["opt1", "opt2", "opt3", "opt4"]}}"""
    },
    {
        "stage": 7,
        "dimension": "urgency_and_readiness",
        "description": "Urgency, prior attempts, readiness to act.",
        "prompt": """You are a diagnostic tool helping a team leader articulate a business problem.
You are at Stage 7: Urgency & Readiness. This is the final question.

{company_context}

Based on everything {first_name} has shared, ask ONE closing question.
Cover urgency, what's been tried before, and readiness to act.
Use "selection" — structured options help close the diagnostic cleanly.

Respond ONLY with valid JSON:
{{"question_text": "your question", "response_type": "selection", "options": ["opt1", "opt2", "opt3", "opt4"]}}"""
    },
]

# Legacy hardcoded framework prompt retained for rollback reference.
# GENSYN_FRAMEWORK = """
# You are an expert organizational diagnostician working for Gensyn Design, a management consultancy specializing in strategy and problem solving.
#
# Gensyn categorizes organizational problems into three core types:
# 1. ALIGNMENT PROBLEMS — The issue is understood and solutions exist, but the team cannot converge on a path forward.
# 2. CLARITY PROBLEMS — The issue is felt but not well-defined. No clear solutions are on the table because the problem itself hasn't been properly scoped.
# 3. EXECUTION PROBLEMS — The issue is understood and a path has been chosen, but the team cannot make progress.
#
# Gensyn's two core workshop offerings:
# - LIGHTNING DECISION JAM (LDJ): Best for ALIGNMENT problems. Structured, time-boxed convergence when solutions exist but the team can't agree.
# - GENSYN JUMPSTART: Best for CLARITY problems. Facilitated exploration when the team needs to figure out where to begin.
#
# When analyzing:
# - Use the user's first name sparingly (at most once)
# - Reference their company and role specifically
# - Be specific to what they described — never generic
# - Name the problem type clearly
# - Explain WHY this type of stuck matters
# - Connect the recommendation logically to their situation
# - If ambiguous, say so honestly and explain both options
# - Tone: direct, considered, respectful — not salesy
# """


def generate_next_question(stage_number: int, previous_answers: list, company_context: dict = None, user_info: dict = None) -> dict:
    """Generate the next diagnostic question using Haiku."""
    if stage_number < 1 or stage_number > len(STAGES):
        return None

    stage = STAGES[stage_number - 1]
    client = get_anthropic_client()

    # Build company context string
    context_str = ""
    if company_context and company_context.get("known"):
        context_str = f"""Company context:
- Company: {company_context.get('description', 'Unknown')}
- Industry: {company_context.get('industry', 'Unknown')}
- Size: {company_context.get('approximate_size', 'Unknown')}
Use this to make questions more relevant."""
    elif stage_number <= 2:
        context_str = "You don't have info about this company. Naturally invite them to briefly describe what their organization does as part of their answer."
    else:
        context_str = "Limited company info — rely on what the user has shared."

    # Get user's first name
    first_name = "there"
    if user_info and user_info.get("first_name"):
        first_name = clean_name(user_info["first_name"])

    # Build previous answers context
    answers_str = ""
    if previous_answers:
        answers_str = "\n\nWhat the user has shared so far:\n"
        for answer in previous_answers:
            answers_str += f"- Stage {answer['stage']} ({answer['dimension']}): Q: \"{answer['question_text']}\" → A: \"{answer['response_value']}\"\n"

    # Insert context into prompt
    prompt = stage["prompt"].replace("{company_context}", context_str).replace("{first_name}", first_name)

    last_error = None
    for attempt in range(3):
        try:
            retry_instruction = ""
            if attempt > 0:
                retry_instruction = "\n\nYour previous answer did not parse as valid JSON. Return ONLY strict JSON matching the schema."

            message = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": prompt + answers_str + retry_instruction
                }]
            )

            response_text = _strip_code_fences(message.content[0].text)
            question_data = json.loads(response_text)
            question_data["stage"] = stage_number
            question_data["dimension"] = stage["dimension"]
            question_data["total_stages"] = len(STAGES)
            return question_data
        except Exception as exc:
            last_error = exc
            continue

    # Safe fallback to avoid transient stage failures blocking flow
    if "selection" in stage["prompt"]:
        return {
            "question_text": "Which option best describes your situation right now?",
            "response_type": "selection",
            "options": [
                "This affects a small part of the team",
                "This affects multiple teams",
                "This affects most of the organization",
                "This is critical and urgent across the organization",
            ],
            "stage": stage_number,
            "dimension": stage["dimension"],
            "total_stages": len(STAGES),
        }

    return {
        "question_text": "Can you share a bit more detail about your situation?",
        "response_type": "short_text",
        "options": None,
        "stage": stage_number,
        "dimension": stage["dimension"],
        "total_stages": len(STAGES),
        "error": str(last_error) if last_error else None,
    }


def generate_analysis(responses: list, mode: str = "public", company_context: dict = None, user_info: dict = None) -> dict:
    """Generate the final analysis and recommendation using Sonnet."""
    client = get_anthropic_client()
    framework_context = build_framework_context(responses)

    # User details
    first_name = clean_name(user_info.get("first_name", "")) if user_info else ""
    last_name = clean_name(user_info.get("last_name", "")) if user_info else ""
    role = user_info.get("role", "") if user_info else ""
    organization = user_info.get("organization", "") if user_info else ""

    # Company context
    company_str = ""
    if company_context and company_context.get("known"):
        company_str = f"\nCompany: {organization} — {company_context.get('description', '')} (Industry: {company_context.get('industry', '')}, Size: {company_context.get('approximate_size', '')})"

    # Response summary
    response_summary = ""
    for r in responses:
        response_summary += f"Stage {r['stage']} ({r['dimension']}): \"{r['question_text']}\" → \"{r['response_value']}\"\n"

    mode_instruction = ""
    if mode == "public":
        mode_instruction = """Recommend one workshop using these rules:
- First check special matches (these take priority):
  - External + Insight -> Customer Insights Workshop
  - Internal + Experimentation -> Interactive Process Simulation
  - Transitional + Execution -> Scenario Planning
- If no special match applies, use general matching:
  - Clarity or Coherence -> Lightning Decision Jam
  - Insight or Experimentation -> Gensyn Jumpstart
  - Connection or Execution -> Games Event Workshop
  - Momentum -> Gensyn Jumpstart
Always tie the recommendation to the identified challenge type and dynamic."""
    else:
        mode_instruction = """Do NOT recommend a workshop for referred mode.
Set "workshop_recommendation" to null and keep "recommendation_explanation" brief."""

    prompt = f"""You are an expert organizational diagnostician working for Gensyn Design, a management consultancy specializing in strategy and problem solving.

Use the following Gensyn frameworks to guide your analysis:

{framework_context}

The user is {first_name} {last_name}, {role} at {organization}.{company_str}

Their diagnostic responses:

{response_summary}

Your task:
1) Identify the PRIMARY challenge type from this spectrum (upstream to downstream):
- connection (working together as a team)
- clarity (uniting multiple perspectives)
- coherence (aligning to a shared purpose)
- insight (surfacing new information)
- experimentation (trying new ideas)
- execution (moving forward productively)
- momentum (getting unstuck)

2) Apply the upstream principle: pick the earliest broken link. If downstream issues exist but an upstream issue is present, choose the upstream one.

3) Identify the PRIMARY challenge dynamic:
- internal (team, culture, process)
- external (market, customer, partners)
- transitional (change, growth, disruption)

4) Use the framework context above rather than generic consulting language.

Output style requirements:
- Direct, considered, respectful; not salesy
- Basic but accurate over complex and wordy
- Specific to what they said; never invent details
- If ambiguous, say so honestly
- Keep it concise

{mode_instruction}

Respond ONLY with valid JSON:
{{
    "challenge_type": "connection | clarity | coherence | insight | experimentation | execution | momentum",
    "challenge_dynamic": "internal | external | transitional",
    "problem_summary": "1-2 sentences. Specific to their situation, not generic.",
    "analysis": "1 short paragraph. What this means for them specifically. Reference what they said. Do not pad with generic advice.",
    "workshop_recommendation": "Lightning Decision Jam | Gensyn Jumpstart | Games Event Workshop | Customer Insights Workshop | Interactive Process Simulation | Scenario Planning | null",
    "recommendation_explanation": "2-3 sentences. Why this workshop fits their specific challenge type and dynamic.",
    "suggested_next_steps": ["step 1", "step 2", "step 3"]
}}"""

    message = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]

    analysis = json.loads(response_text)
    # Backward-compatible aliases so existing consumers continue to work.
    analysis["problem_type"] = analysis.get("challenge_type")
    analysis["problem_type_explanation"] = (
        f"Primary dynamic: {analysis.get('challenge_dynamic', 'unknown')}."
    )
    return analysis
