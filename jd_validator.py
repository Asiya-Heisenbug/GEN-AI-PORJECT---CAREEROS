from typing import Any


JD_FIELDS = {
    "job_title": None,
    "company": None,
    "location": None,
    "employment_type": None,
    "summary": None,
    "technical_skills": [],
    "soft_skills": [],
    "responsibilities": [],
    "qualifications": [],
    "preferred_qualifications": [],
    "experience_requirements": [],
    "education_requirements": [],
    "certifications": [],
    "keywords": [],
}


def validate_job_data(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Job description data must be a JSON object.")

    normalized = dict(data)
    for key, default in JD_FIELDS.items():
        normalized.setdefault(key, default)
    for field, default in JD_FIELDS.items():
        if isinstance(default, list) and not isinstance(normalized[field], list):
            normalized[field] = []
    return normalized