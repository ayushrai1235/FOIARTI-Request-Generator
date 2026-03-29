"""
n8n_client.py — n8n webhook integration for FOIA/RTI Request Generator.

Handles POST requests to the n8n webhook endpoint after letter generation.
Designed to fail gracefully — n8n errors never crash the CLI.
"""

import os

import click
import requests as req
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


def trigger_n8n(payload: dict) -> bool:
    """
    Send a webhook POST request to n8n with the request payload.

    The payload follows the schema defined in TRD §4.4:
    {
        "request_id": "FOIA-2025-A7F3C2D1",
        "agency_name": "U.S. Department of Agriculture",
        "agency_email": "ams.foia@usda.gov",
        "jurisdiction": "federal",
        "subject": "Slaughterhouse inspection records Iowa 2023",
        "requester_name": "Jane Doe",
        "date_sent": "2025-01-15",
        "response_due": "2025-02-14",
        "letter_text": "...(full letter)...",
        "output_file": "output/FOIA-2025-A7F3C2D1.txt"
    }

    Args:
        payload: Dictionary containing request metadata and letter text.

    Returns:
        True if webhook was successfully triggered, False otherwise.
    """
    url = os.getenv(
        "N8N_WEBHOOK_URL",
        "http://localhost:5678/webhook/foia-request",
    )
    enabled = os.getenv("N8N_ENABLED", "true").lower() == "true"

    if not enabled:
        click.echo(
            click.style(
                "  ℹ  n8n integration disabled → skipped",
                fg="yellow",
            )
        )
        return False

    try:
        resp = req.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            click.echo(
                click.style(
                    "  ✓  n8n notified → webhook triggered",
                    fg="magenta",
                )
            )
            return True
        else:
            click.echo(
                click.style(
                    f"  ⚠  n8n warning → HTTP {resp.status_code}",
                    fg="yellow",
                )
            )
            return False
    except req.exceptions.ConnectionError:
        click.echo(
            click.style(
                "  ⚠  n8n offline → skipped (letter still saved)",
                fg="yellow",
            )
        )
        return False
    except req.exceptions.Timeout:
        click.echo(
            click.style(
                "  ⚠  n8n timeout → skipped (letter still saved)",
                fg="yellow",
            )
        )
        return False
    except Exception:
        click.echo(
            click.style(
                "  ⚠  n8n error → skipped (letter still saved)",
                fg="yellow",
            )
        )
        return False
