from typing import Any
import os

from ai_analyzer import analyze_with_ollama


JD_SYSTEM_PROMPT = """Extract a job description into valid JSON with exactly these keys:
job_title, company, location, employment_type, summary, technical_skills, soft_skills,
responsibilities, qualifications, preferred_qualifications, experience_requirements,
education_requirements, certifications, keywords.
Use null for unknown scalar values and [] for unknown lists. Preserve every requirement and
technology mentioned in the job description. Do not invent details."""


def analyze_job_description(job_description: str) -> dict[str, Any]:
    return analyze_with_ollama(
        job_description,
        JD_SYSTEM_PROMPT,
        model=os.getenv("OLLAMA_EXTRACTION_MODEL", "llama3.2"),
    )