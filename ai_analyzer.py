import json
import os
import base64
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def _setting(name: str, default: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except (FileNotFoundError, KeyError):
        return default


SYSTEM_PROMPT = """You are a meticulous resume analyst. Extract EVERY visible fact from every page.
Return only valid JSON with these keys: name, email, phone, location, links, summary, skills,
experience, education, projects, internships, certifications, achievements, publications,
coursework, languages, strengths, weaknesses, missing_information, raw_evidence.
Preserve exact dates, metrics, technologies, job titles, company names, project names, and bullet
details. Use null for unknown scalar values and [] for unknown lists. Do not invent information.
Attached page images are authoritative; supplemental text may have lost layout and columns."""


def analyze_with_ollama(
    text: str,
    system_prompt: str,
    images: list[bytes] | None = None,
    model: str | None = None,
    json_mode: bool = True,
) -> dict[str, Any] | str:
    image_payload = [base64.b64encode(image).decode("ascii") for image in (images or [])]
    user_message: dict[str, Any] = {"role": "user", "content": text}
    if image_payload:
        user_message["images"] = image_payload
    payload = json.dumps(
        {
            "model": model or _setting("OLLAMA_EXTRACTION_MODEL", "llama3.2"),
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                user_message,
            ],
        }
    ).encode("utf-8")
    payload_data = json.loads(payload.decode("utf-8"))
    if json_mode:
        payload_data["format"] = "json"
    else:
        payload_data["options"] = {"temperature": 0.2}
    payload = json.dumps(payload_data).encode("utf-8")
    request = Request(
        f"{_setting('OLLAMA_HOST', 'http://localhost:11434').rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    timeout = int(_setting("OLLAMA_TIMEOUT_SECONDS", "900"))
    try:
        with urlopen(request, timeout=timeout) as response:
            content = json.loads(response.read().decode("utf-8")).get("message", {}).get("content")
    except HTTPError as error:
        if error.code == 404:
            raise RuntimeError(f"Ollama model not found: {model or _setting('OLLAMA_EXTRACTION_MODEL', 'llama3.2')}") from error
        raise RuntimeError(f"Ollama returned HTTP {error.code}.") from error
    except URLError as error:
        raise RuntimeError("Could not connect to Ollama. Start it with: ollama serve") from error
    except TimeoutError as error:
        raise RuntimeError(
            f"Ollama timed out after {timeout} seconds. The vision model may still be loading; "
            "try again or increase OLLAMA_TIMEOUT_SECONDS in .env."
        ) from error

    if not content:
        raise ValueError("Ollama returned an empty response.")

    if not json_mode:
        return content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("Ollama returned invalid JSON.") from error

    if not isinstance(result, dict):
        raise ValueError("The analyzer response must be a JSON object.")
    return result


def analyze_resume(resume_text: str, images: list[bytes] | None = None) -> dict[str, Any]:
    return analyze_with_ollama(
        resume_text,
        SYSTEM_PROMPT,
        model=_setting("OLLAMA_EXTRACTION_MODEL", "llama3.2"),
    )


def analyze_comparison(
    profile: dict[str, Any],
    job: dict[str, Any],
    github_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = """Compare the complete candidate profile and complete job description. Return only JSON with:
overall_fit_score (0-100), matched_skills, partial_matches, missing_skills, strongest_evidence,
gaps, recommended_projects, interview_topics, explanation.
CANDIDATE PROFILE:
{profile}
JOB DESCRIPTION:
{job}
GITHUB PROJECTS:
{github}"""
    return analyze_with_ollama(
        prompt.format(profile=json.dumps(profile), job=json.dumps(job), github=json.dumps(github_context or {})),
        "You are a rigorous hiring analyst. Use only supplied facts.",
        model=_setting("OLLAMA_MATCHING_MODEL", "qwen2.5vl:7b"),
    )


def answer_question(
    question: str,
    profile: dict[str, Any],
    job: dict[str, Any],
    comparison: dict[str, Any],
    github_context: dict[str, Any] | None = None,
) -> str:
    prompt = """Answer the user's question using only the candidate profile, job description, and comparison.
If a fact is absent, say so. Give specific evidence and practical advice.
PROFILE: {profile}
JOB: {job}
COMPARISON: {comparison}
    GITHUB PROJECTS:
    {github}
    QUESTION: {question}

Rules: Answer in normal Markdown prose, never JSON. If the user says they cannot relocate,
evaluate location explicitly. For project recommendations, inspect the GitHub project evidence
and name the best project plus why it fits the JD. Do not claim you searched GitHub unless project
data is supplied."""
    result = analyze_with_ollama(
        prompt.format(profile=json.dumps(profile), job=json.dumps(job), comparison=json.dumps(comparison), github=json.dumps(github_context or {}), question=question),
        "You are a practical career coach grounded in supplied resume, JD, comparison, and GitHub evidence.",
        model=_setting("OLLAMA_MATCHING_MODEL", "qwen2.5vl:7b"),
        json_mode=False,
    )
    return str(result)
