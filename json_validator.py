from typing import Any


REQUIRED_FIELDS = {
    "name": None,
    "email": None,
    "phone": None,
    "location": None,
    "summary": None,
    "skills": [],
    "experience": [],
    "education": [],
}


def validate_resume_data(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize the analyzer response to the application's stable shape."""
    if not isinstance(data, dict):
        raise ValueError("Resume data must be a JSON object.")

    normalized = dict(data)
    for key, default in REQUIRED_FIELDS.items():
        normalized.setdefault(key, default)

    for field in ("skills", "experience", "education"):
        if not isinstance(normalized[field], list):
            normalized[field] = []

    return normalized
