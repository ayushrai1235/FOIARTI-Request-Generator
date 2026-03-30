"""
n8n_client.py — Webhook trigger for n8n automation workflows.
Fails gracefully — n8n errors never crash the CLI.
"""
import os
import click
import requests as req
from dotenv import load_dotenv

load_dotenv()


def trigger_n8n(payload: dict) -> bool:
    """
    POST the request payload to the n8n PRODUCTION webhook URL.

    Uses the production URL (not webhook-test) so the workflow:
    - Stays active and accepts all 5 demo requests continuously
    - Does not stop after one execution
    - Auto-triggers every time python demo.py runs

    Returns True if notified successfully, False otherwise.
    """
    url = os.getenv(
        "N8N_WEBHOOK_URL",
        "https://ayushrai2222.app.n8n.cloud/webhook/foia-request",
    )
    enabled = os.getenv("N8N_ENABLED", "true").lower() == "true"

    if not enabled:
        click.echo(click.style(
            "  o  n8n disabled → skipped (N8N_ENABLED=false)", fg="cyan"
        ))
        return False

    # Warn if someone accidentally uses the test URL
    if "webhook-test" in url:
        click.echo(click.style(
            "  !  WARNING: You are using the TEST webhook URL.\n"
            "     It only accepts ONE request then stops.\n"
            "     Change N8N_WEBHOOK_URL to use /webhook/ not /webhook-test/",
            fg="yellow",
        ))

    click.echo(click.style(
        f"  >  Sending to n8n: {url}", fg="cyan"
    ))

    try:
        resp = req.post(url, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            click.echo(click.style(
                f"  OK  n8n notified → webhook triggered (HTTP {resp.status_code})",
                fg="magenta",
            ))
            return True
        else:
            click.echo(click.style(
                f"  !  n8n warning → HTTP {resp.status_code}: {resp.text[:120]}",
                fg="yellow",
            ))
            return False

    except req.exceptions.ConnectionError:
        click.echo(click.style(
            "  !  n8n unreachable → check your N8N_WEBHOOK_URL in .env\n"
            "     Letter is still saved locally.",
            fg="yellow",
        ))
        return False
    except req.exceptions.Timeout:
        click.echo(click.style(
            "  !  n8n timeout (>10s) → letter still saved locally.",
            fg="yellow",
        ))
        return False
    except Exception as exc:
        click.echo(click.style(
            f"  !  n8n error → {exc}\n     Letter still saved locally.",
            fg="yellow",
        ))
        return False