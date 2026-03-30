"""
main.py — Click CLI entry point for FOIA/RTI Request Generator.

Supports both flag mode and interactive prompt mode.
Commands: generate (default), --list, --list-agencies, --update-status, demo.
Colored CLI output using click.style().
"""

import json
import sys
from datetime import date
from pathlib import Path

import click
from dotenv import load_dotenv

from generator import generate_letter, load_agencies, load_statutes
from n8n_client import trigger_n8n
from pdf_export import generate_pdf
from tracker import init_db, list_requests, mark_n8n_notified, save_request, update_status


# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Valid jurisdictions
VALID_JURISDICTIONS = ["federal", "california", "texas", "new_york", "india"]


def print_banner():
    """Print the application banner."""
    click.echo()
    click.echo(click.style("╔══════════════════════════════════════════════════╗", fg="blue"))
    click.echo(click.style("║       FOIA/RTI Request Generator v1.0.0         ║", fg="blue"))
    click.echo(click.style("║       Public Records Request Automation         ║", fg="blue"))
    click.echo(click.style("╚══════════════════════════════════════════════════╝", fg="blue"))
    click.echo()


def print_agencies_list():
    """Print all valid agency keys with details."""
    agencies = load_agencies()
    click.echo()
    click.echo(click.style("  Available Agencies:", fg="blue", bold=True))
    click.echo(click.style("  " + "─" * 60, fg="blue"))
    for key, info in agencies.items():
        click.echo(
            f"  {click.style(key, fg='green', bold=True):30s} "
            f"{info['full_name']} ({info['jurisdiction']})"
        )
    click.echo(click.style("  " + "─" * 60, fg="blue"))
    click.echo()


def print_tracking_table():
    """Print the formatted tracking table from the database."""
    try:
        rows = list_requests()
    except Exception as e:
        click.echo(click.style(f"  ✗  Database error: {e}", fg="red"))
        return

    if not rows:
        click.echo(click.style("  ℹ  No tracked requests found.", fg="yellow"))
        return

    click.echo()
    header_line = "─" * 82
    click.echo(click.style(f"  {header_line}", fg="blue"))
    click.echo(
        click.style(
            f"  {'ID':<24} {'AGENCY':<14} {'JURISDICTION':<14} "
            f"{'DATE':<12} {'STATUS':<10}",
            fg="blue",
            bold=True,
        )
    )
    click.echo(click.style(f"  {header_line}", fg="blue"))

    # Status counters
    status_counts = {}

    for row in rows:
        status = row.get("status", "SENT")
        status_counts[status] = status_counts.get(status, 0) + 1

        # Color-code status
        if status == "SENT":
            status_styled = click.style(status, fg="yellow")
        elif status == "RESPONDED":
            status_styled = click.style(status, fg="green")
        elif status == "OVERDUE":
            status_styled = click.style(status, fg="red")
        elif status == "CLOSED":
            status_styled = click.style(status, fg="white")
        else:
            status_styled = click.style(status, fg="cyan")

        click.echo(
            f"  {row['id']:<24} {row['agency_key']:<14} "
            f"{row['jurisdiction']:<14} {row['date_sent']:<12} "
            f"{status_styled:<10}"
        )

    click.echo(click.style(f"  {header_line}", fg="blue"))

    # Summary line
    total = len(rows)
    sent = status_counts.get("SENT", 0)
    responded = status_counts.get("RESPONDED", 0)
    overdue = status_counts.get("OVERDUE", 0)
    closed = status_counts.get("CLOSED", 0)

    click.echo(
        f"  Total: {click.style(str(total), bold=True)}   "
        f"Sent: {click.style(str(sent), fg='yellow')}   "
        f"Responded: {click.style(str(responded), fg='green')}   "
        f"Overdue: {click.style(str(overdue), fg='red')}   "
        f"Closed: {click.style(str(closed), fg='white')}"
    )
    click.echo()


@click.command()
@click.option("--agency", type=str, default=None, help="Agency key (e.g., USDA, FDA).")
@click.option(
    "--jurisdiction",
    type=click.Choice(VALID_JURISDICTIONS, case_sensitive=False),
    default=None,
    help="Jurisdiction for the request.",
)
@click.option("--records", type=str, default=None, help="Description of records sought.")
@click.option("--name", type=str, default=None, help="Your full name for the letter.")
@click.option("--pdf", is_flag=True, default=False, help="Also generate a PDF version.")
@click.option("--list", "list_all", is_flag=True, default=False, help="Show tracking table.")
@click.option(
    "--list-agencies", is_flag=True, default=False, help="Show all valid agency keys."
)
@click.option("--update-status", "update_status_flag", is_flag=True, default=False, help="Update request status.")
@click.option("--id", "request_id", type=str, default=None, help="Request ID for status update.")
@click.option(
    "--status",
    type=click.Choice(
        ["SENT", "RESPONDED", "OVERDUE", "CLOSED", "FOLLOWED_UP"],
        case_sensitive=False,
    ),
    default=None,
    help="New status value.",
)
@click.option("--demo", is_flag=True, default=False, help="Run 5 demo requests.")
def cli(
    agency,
    jurisdiction,
    records,
    name,
    pdf,
    list_all,
    list_agencies,
    update_status_flag,
    request_id,
    status,
    demo,
):
    """FOIA/RTI Request Generator — Generate legally formatted public records requests."""
    print_banner()

    # Initialize database
    try:
        init_db()
    except Exception as e:
        click.echo(click.style(f"  ✗  Database initialization error: {e}", fg="red"))
        click.echo(click.style("  ℹ  Check your DATABASE_URL in .env", fg="yellow"))
        sys.exit(1)

    # --list: Show tracking table
    if list_all:
        click.echo(click.style("  📋 Request Tracking Table", fg="blue", bold=True))
        print_tracking_table()
        return

    # --list-agencies: Show available agencies
    if list_agencies:
        print_agencies_list()
        return

    # --update-status: Update a request's status
    if update_status_flag:
        if not request_id:
            request_id = click.prompt(
                click.style("  Enter Request ID", fg="cyan")
            )
        if not status:
            status = click.prompt(
                click.style("  Enter new status (SENT/RESPONDED/OVERDUE/CLOSED)", fg="cyan")
            )
        try:
            updated = update_status(request_id, status)
            if updated:
                click.echo(
                    click.style(
                        f"  ✓  Status updated: {request_id} → {status.upper()}",
                        fg="green",
                    )
                )
            else:
                click.echo(
                    click.style(
                        f"  ✗  Request ID not found: {request_id}",
                        fg="red",
                    )
                )
        except ValueError as e:
            click.echo(click.style(f"  ✗  {e}", fg="red"))
        except Exception as e:
            click.echo(click.style(f"  ✗  Database error: {e}", fg="red"))
        return

    # --demo: Run demo mode
    if demo:
        from demo import run_demo
        run_demo()
        return

    # --- Generate mode (default) ---

    # Load agencies for validation
    agencies = load_agencies()

    # Interactive prompts if flags not provided
    if not agency:
        print_agencies_list()
        agency = click.prompt(
            click.style("  Enter agency key", fg="cyan")
        )

    # Validate agency
    if agency not in agencies:
        click.echo(click.style(f"  ✗  Unknown agency: '{agency}'", fg="red"))
        print_agencies_list()
        sys.exit(1)

    if not jurisdiction:
        click.echo()
        click.echo(click.style("  Available Jurisdictions:", fg="blue", bold=True))
        for j in VALID_JURISDICTIONS:
            click.echo(f"    • {click.style(j, fg='green')}")
        click.echo()
        jurisdiction = click.prompt(
            click.style("  Enter jurisdiction", fg="cyan")
        )

    # Validate jurisdiction
    if jurisdiction.lower() not in VALID_JURISDICTIONS:
        click.echo(
            click.style(
                f"  ✗  Unknown jurisdiction: '{jurisdiction}'",
                fg="red",
            )
        )
        click.echo(
            click.style(
                f"  ℹ  Valid: {', '.join(VALID_JURISDICTIONS)}",
                fg="yellow",
            )
        )
        sys.exit(1)

    if not records:
        records = click.prompt(
            click.style("  Describe the records you are requesting", fg="cyan")
        )

    if not records or not records.strip():
        click.echo(click.style("  ✗  Records description cannot be empty.", fg="red"))
        sys.exit(1)

    if not name:
        name = click.prompt(
            click.style("  Enter your full name", fg="cyan")
        )

    # Generate the letter
    click.echo()
    click.echo(click.style("  ⏳ Generating request letter...", fg="yellow"))

    try:
        letter_text, req_id, response_due = generate_letter(
            agency_key=agency,
            jurisdiction=jurisdiction.lower(),
            records_description=records,
            requester_name=name,
        )
    except ValueError as e:
        click.echo(click.style(f"  ✗  {e}", fg="red"))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"  ✗  Generation failed: {e}", fg="red"))
        sys.exit(1)

    # Save output files
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save .txt
    txt_path = output_dir / f"{req_id}.txt"
    txt_path.write_text(letter_text, encoding="utf-8")
    click.echo(click.style(f"  ✓  Letter saved → {txt_path}", fg="green"))

    # Save .pdf (optional)
    if pdf:
        pdf_path = output_dir / f"{req_id}.pdf"
        try:
            generate_pdf(letter_text, req_id, str(pdf_path))
            click.echo(click.style(f"  ✓  PDF saved  → {pdf_path}", fg="green"))
        except Exception as e:
            click.echo(click.style(f"  ⚠  PDF generation failed: {e}", fg="yellow"))

    # Track in database
    agency_data = agencies[agency]
    try:
        save_request(
            request_id=req_id,
            agency_key=agency,
            agency_name=agency_data["full_name"],
            jurisdiction=jurisdiction.lower(),
            subject=records[:100],
            requester_name=name,
            date_sent=date.today().isoformat(),
            response_due=response_due,
            output_file=str(txt_path),
        )
        click.echo(click.style(f"  ✓  Tracked    → {req_id}", fg="green"))
    except Exception as e:
        click.echo(click.style(f"  ⚠  Tracking failed: {e}", fg="yellow"))
        click.echo(click.style("  ℹ  Letter was still saved to output/", fg="yellow"))

    # Trigger n8n webhook
    try:
        n8n_payload = {
            "request_id": req_id,
            "agency_name": agency_data["full_name"],
            "agency_email": agency_data["foia_email"],
            "jurisdiction": jurisdiction.lower(),
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
                "  ⚠  n8n offline → skipped (letter still saved)",
                fg="yellow",
            )
        )

    # Print letter preview
    click.echo()
    click.echo(click.style("  📄 Letter Preview (first 800 chars):", fg="blue", bold=True))
    click.echo(click.style("  " + "─" * 60, fg="blue"))
    preview = letter_text[:800]
    for line in preview.split("\n"):
        click.echo(f"  {line}")
    if len(letter_text) > 800:
        click.echo(click.style("  ... [truncated]", fg="yellow"))
    click.echo(click.style("  " + "─" * 60, fg="blue"))

    # Final summary
    click.echo()
    click.echo(click.style("  ═══ Summary ═══", fg="blue", bold=True))
    click.echo(f"  Request ID   : {click.style(req_id, fg='green', bold=True)}")
    click.echo(f"  Agency       : {agency_data['full_name']}")
    click.echo(f"  Jurisdiction : {jurisdiction}")
    click.echo(f"  Date Sent    : {date.today().isoformat()}")
    click.echo(f"  Response Due : {response_due}")
    click.echo(f"  Output       : {txt_path}")
    if pdf:
        click.echo(f"  PDF          : {output_dir / f'{req_id}.pdf'}")
    click.echo()


if __name__ == "__main__":
    cli()
