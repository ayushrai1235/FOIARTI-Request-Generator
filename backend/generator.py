"""
generator.py — Letter generation logic for FOIA/RTI Request Generator.

Loads agency and statute data from JSON files, generates unique request IDs,
calculates response deadlines, and renders Jinja2 templates into complete
legally formatted request letters.
"""

import json
import uuid
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


# Base directory (where this script lives)
BASE_DIR = Path(__file__).resolve().parent


def load_agencies() -> dict:
    """Load and return the agencies dictionary from agencies.json."""
    agencies_path = BASE_DIR / "agencies.json"
    with open(agencies_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_statutes() -> dict:
    """Load and return the statutes dictionary from statutes.json."""
    statutes_path = BASE_DIR / "statutes.json"
    with open(statutes_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_request_id(prefix: str) -> str:
    """
    Generate a unique request ID in the format:
    {PREFIX}-{YEAR}-{UUID8_UPPERCASE}

    Examples:
        FOIA-2025-A7F3C2D1
        RTI-2025-E3B6D1C9
    """
    year = date.today().year
    unique = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{year}-{unique}"


def calculate_response_due(response_days: int, day_type: str) -> str:
    """
    Calculate the response deadline from today.

    Args:
        response_days: Number of days the agency has to respond.
        day_type: Either 'business' or 'calendar'.

    Returns:
        ISO-formatted date string (YYYY-MM-DD) and human-readable string.
    """
    today = date.today()

    if day_type == "business":
        # Skip weekends (Saturday=5, Sunday=6)
        added = 0
        current = today
        while added < response_days:
            current += timedelta(days=1)
            if current.weekday() < 5:  # Monday-Friday
                added += 1
        due_date = current
    else:
        # Calendar days — direct addition
        due_date = today + timedelta(days=response_days)

    return due_date.strftime("%Y-%m-%d"), due_date.strftime("%B %d, %Y")


def generate_letter(
    agency_key: str,
    jurisdiction: str,
    records_description: str,
    requester_name: str,
) -> tuple:
    """
    Generate a complete FOIA/RTI request letter.

    Args:
        agency_key: Key from agencies.json (e.g., 'USDA', 'FDA').
        jurisdiction: One of 'federal', 'california', 'texas', 'new_york', 'india'.
        records_description: Description of the records being requested.
        requester_name: Name of the person making the request.

    Returns:
        Tuple of (letter_text, request_id, response_due_iso)

    Raises:
        ValueError: If agency_key or jurisdiction is invalid.
    """
    agencies = load_agencies()
    statutes = load_statutes()

    # Validate agency
    if agency_key not in agencies:
        valid_keys = ", ".join(sorted(agencies.keys()))
        raise ValueError(
            f"Unknown agency key: '{agency_key}'. "
            f"Valid agencies: {valid_keys}"
        )

    # Validate jurisdiction
    if jurisdiction not in statutes:
        valid_jurisdictions = ", ".join(sorted(statutes.keys()))
        raise ValueError(
            f"Unknown jurisdiction: '{jurisdiction}'. "
            f"Valid jurisdictions: {valid_jurisdictions}"
        )

    agency = agencies[agency_key]
    statute = statutes[jurisdiction]

    # Generate unique request ID
    prefix = statute["letter_prefix"]
    request_id = generate_request_id(prefix)

    # Calculate response deadline
    response_due_iso, response_due_human = calculate_response_due(
        statute["response_days"], statute["response_day_type"]
    )

    # Set up Jinja2 environment
    template_dir = BASE_DIR / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
    )

    template_file = statute["template"]
    template = env.get_template(template_file)

    # Prepare template variables
    template_vars = {
        "request_id": request_id,
        "date": date.today().strftime("%B %d, %Y"),
        "agency_officer": agency["foia_officer"],
        "agency_full_name": agency["full_name"],
        "agency_address": agency["mailing_address"],
        "agency_city_state_zip": agency["city_state_zip"],
        "agency_email": agency["foia_email"],
        "law_name": statute["law_name"],
        "citation": statute["citation"],
        "fee_waiver_citation": statute["fee_waiver_citation"],
        "exemption_citation": statute["exemption_citation"],
        "records_description": records_description,
        "response_days": statute["response_days"],
        "response_day_type": statute["response_day_type"],
        "response_due": response_due_human,
        "requester_name": requester_name,
    }

    # Render the template
    letter_text = template.render(**template_vars)

    # Verify no unfilled placeholders remain
    if "{{" in letter_text and "}}" in letter_text:
        raise RuntimeError(
            f"Template rendering incomplete — unfilled placeholders detected "
            f"in template '{template_file}'."
        )

    return letter_text, request_id, response_due_iso
