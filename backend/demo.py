"""
demo.py — Runs 5 predefined FOIA/RTI requests covering all jurisdictions.

Demonstrates the full workflow: letter generation, file output, database
tracking, and n8n webhook triggering.
"""

import sys
from datetime import date
from pathlib import Path

import click

from generator import generate_letter, load_agencies
from n8n_client import trigger_n8n
from pdf_export import generate_pdf
from tracker import init_db, mark_n8n_notified, save_request


# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Predefined demo requests covering all 5 jurisdictions
DEMO_REQUESTS = [
    {
        "agency": "USDA",
        "jurisdiction": "federal",
        "records": (
            "All inspection reports, non-compliance records, and enforcement "
            "actions for federally inspected slaughterhouses in Iowa for the "
            "period January 1, 2023 through December 31, 2024"
        ),
        "name": "Demo Requester",
    },
    {
        "agency": "FDA",
        "jurisdiction": "federal",
        "records": (
            "All pesticide residue monitoring program test results, surveillance "
            "reports, import alerts, and refusal-of-admission records concerning "
            "pesticide residues on imported fresh produce for fiscal years 2022, "
            "2023, and 2024"
        ),
        "name": "Demo Requester",
    },
    {
        "agency": "CA_CDFA",
        "jurisdiction": "california",
        "records": (
            "All dairy farm inspection reports, notices of violation, and "
            "corrective action orders for dairy operations in Fresno County, "
            "California for the period January 1, 2023 through December 31, 2024"
        ),
        "name": "Demo Requester",
    },
    {
        "agency": "TX_DSHS",
        "jurisdiction": "texas",
        "records": (
            "All foodborne illness outbreak investigation reports, "
            "epidemiological summaries, laboratory confirmation records, and "
            "correspondence with the CDC related to outbreaks investigated by "
            "the DSHS Consumer Protection Division in Texas from January 1, "
            "2023 through December 31, 2024"
        ),
        "name": "Demo Requester",
    },
    {
        "agency": "India_MoAFW",
        "jurisdiction": "india",
        "records": (
            "All registration certificates, technical evaluation reports, and "
            "correspondence between the Central Insecticides Board and "
            "Registration Committee (CIB&RC) and applicant companies for "
            "pesticides approved under the Insecticides Act, 1968 during the "
            "period April 1, 2020 to March 31, 2024"
        ),
        "name": "Demo Requester",
    },
]


def run_demo():
    """
    Execute all 5 demo requests sequentially.

    For each request:
    1. Generate the letter using the correct template
    2. Save .txt output to output/
    3. Track in the database
    4. Trigger n8n webhook
    5. Print progress

    Prints final summary: "X/5 requests generated successfully"
    """
    click.echo()
    click.echo(
        click.style(
            "  🚀 DEMO MODE — Generating 5 requests across all jurisdictions",
            fg="blue",
            bold=True,
        )
    )
    click.echo(click.style("  " + "═" * 60, fg="blue"))
    click.echo()

    # Initialize database
    try:
        init_db()
    except Exception as e:
        click.echo(click.style(f"  ✗  Database initialization error: {e}", fg="red"))
        click.echo(click.style("  ℹ  Check your DATABASE_URL in .env", fg="yellow"))
        sys.exit(1)

    agencies = load_agencies()
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(DEMO_REQUESTS)

    for i, req_data in enumerate(DEMO_REQUESTS, 1):
        agency_key = req_data["agency"]
        jurisdiction = req_data["jurisdiction"]
        records = req_data["records"]
        name = req_data["name"]

        click.echo(
            click.style(
                f"  [{i}/{total}] {agency_key} ({jurisdiction})",
                fg="cyan",
                bold=True,
            )
        )

        try:
            # Generate letter
            letter_text, req_id, response_due = generate_letter(
                agency_key=agency_key,
                jurisdiction=jurisdiction,
                records_description=records,
                requester_name=name,
            )
            click.echo(
                click.style(f"    ✓  Generated → {req_id}", fg="green")
            )

            # Save .txt
            txt_path = output_dir / f"{req_id}.txt"
            txt_path.write_text(letter_text, encoding="utf-8")
            click.echo(
                click.style(f"    ✓  Saved     → {txt_path.name}", fg="green")
            )

            # Track in database
            agency_data = agencies[agency_key]
            try:
                save_request(
                    request_id=req_id,
                    agency_key=agency_key,
                    agency_name=agency_data["full_name"],
                    jurisdiction=jurisdiction,
                    subject=records[:100],
                    requester_name=name,
                    date_sent=date.today().isoformat(),
                    response_due=response_due,
                    output_file=str(txt_path),
                )
                click.echo(
                    click.style(f"    ✓  Tracked   → database", fg="green")
                )
            except Exception as e:
                click.echo(
                    click.style(f"    ⚠  Tracking failed: {e}", fg="yellow")
                )

            # Trigger n8n
            try:
                n8n_payload = {
                    "request_id": req_id,
                    "agency_name": agency_data["full_name"],
                    "agency_email": agency_data["foia_email"],
                    "jurisdiction": jurisdiction,
                    "subject": records[:100],
                    "requester_name": name,
                    "date_sent": date.today().isoformat(),
                    "response_due": response_due,
                    "letter_text": letter_text,
                    "output_file": str(txt_path),
                }
                n8n_success = trigger_n8n(n8n_payload)
                if n8n_success:
                    try:
                        mark_n8n_notified(req_id)
                    except Exception:
                        pass
            except Exception:
                click.echo(
                    click.style(
                        "    ⚠  n8n skipped",
                        fg="yellow",
                    )
                )

            success_count += 1

        except Exception as e:
            click.echo(click.style(f"    ✗  Failed: {e}", fg="red"))

        click.echo()

    # Final summary
    click.echo(click.style("  " + "═" * 60, fg="blue"))
    if success_count == total:
        click.echo(
            click.style(
                f"  ✅ {success_count}/{total} requests generated successfully",
                fg="green",
                bold=True,
            )
        )
    else:
        click.echo(
            click.style(
                f"  ⚠  {success_count}/{total} requests generated "
                f"({total - success_count} failed)",
                fg="yellow",
                bold=True,
            )
        )
    click.echo()


if __name__ == "__main__":
    run_demo()
