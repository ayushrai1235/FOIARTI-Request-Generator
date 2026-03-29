# Master Build Prompt
## FOIA/RTI Request Generator CLI Tool

Paste this entire prompt into Claude (or any LLM) to generate the complete application.

---

## PROMPT START

Build a complete Python CLI application called the **FOIA/RTI Request Generator**. Generate every file listed below, fully working, with no placeholders or TODOs. Follow every specification exactly.

---

### What the app does

A command-line tool that takes an agency name, jurisdiction, and description of records sought, and produces a properly formatted FOIA or RTI request letter with:
- Correct legal citations per jurisdiction
- The correct mailing address and email for that agency's FOIA/RTI office
- A fee waiver justification paragraph
- A unique tracking ID, saved to SQLite

---

### Files to generate

Generate ALL of the following files completely:

1. `main.py` — Click CLI entry point
2. `generator.py` — Letter generation logic
3. `tracker.py` — SQLite tracking
4. `demo.py` — Runs 5 demo requests
5. `pdf_export.py` — PDF generation with reportlab
6. `agencies.json` — 5 agencies with full address data
7. `statutes.json` — 5 jurisdictions with full statute data
8. `templates/foia_federal.txt` — Jinja2 template
9. `templates/foia_california.txt` — Jinja2 template
10. `templates/foia_texas.txt` — Jinja2 template
11. `templates/foia_new_york.txt` — Jinja2 template
12. `templates/rti_india.txt` — Jinja2 template
13. `requirements.txt`
14. `.env.example`
15. `README.md`

---

### Exact specifications

#### agencies.json — use these exact values:

```json
{
  "USDA": {
    "full_name": "U.S. Department of Agriculture",
    "jurisdiction": "federal",
    "foia_officer": "FOIA Officer",
    "foia_email": "ams.foia@usda.gov",
    "mailing_address": "1400 Independence Ave SW",
    "city_state_zip": "Washington, DC 20250",
    "online_portal": "efoia.usda.gov"
  },
  "FDA": {
    "full_name": "U.S. Food and Drug Administration",
    "jurisdiction": "federal",
    "foia_officer": "FOIA Staff",
    "foia_email": "fdafoia@fda.hhs.gov",
    "mailing_address": "5630 Fishers Lane, Room 1035",
    "city_state_zip": "Rockville, MD 20857",
    "online_portal": "fda.hhs.gov/regulatory-information/foia"
  },
  "CA_CDFA": {
    "full_name": "California Department of Food and Agriculture",
    "jurisdiction": "california",
    "foia_officer": "Public Records Coordinator",
    "foia_email": "publicrecords@cdfa.ca.gov",
    "mailing_address": "1220 N Street",
    "city_state_zip": "Sacramento, CA 95814",
    "online_portal": "cdfa.ca.gov"
  },
  "TX_DSHS": {
    "full_name": "Texas Department of State Health Services",
    "jurisdiction": "texas",
    "foia_officer": "Open Records Coordinator",
    "foia_email": "dshs.openrecords@dshs.texas.gov",
    "mailing_address": "P.O. Box 149347",
    "city_state_zip": "Austin, TX 78714-9347",
    "online_portal": "dshs.texas.gov"
  },
  "India_MoAFW": {
    "full_name": "Ministry of Agriculture and Farmers Welfare",
    "jurisdiction": "india",
    "foia_officer": "Central Public Information Officer",
    "foia_email": "rti-moafw@nic.in",
    "mailing_address": "Krishi Bhawan, Dr. Rajendra Prasad Road",
    "city_state_zip": "New Delhi - 110 001",
    "online_portal": "rtionline.gov.in"
  }
}
```

#### statutes.json — use these exact values:

```json
{
  "federal": {
    "law_name": "Freedom of Information Act",
    "short_name": "FOIA",
    "citation": "5 U.S.C. § 552",
    "fee_waiver_citation": "5 U.S.C. § 552(a)(4)(A)(iii)",
    "exemption_citation": "5 U.S.C. § 552(b)",
    "response_days": 20,
    "response_day_type": "business",
    "letter_prefix": "FOIA",
    "template": "foia_federal.txt"
  },
  "california": {
    "law_name": "California Public Records Act",
    "short_name": "CPRA",
    "citation": "Cal. Gov. Code § 7920 et seq.",
    "fee_waiver_citation": "Cal. Gov. Code § 7922.530",
    "exemption_citation": "Cal. Gov. Code § 7927.700",
    "response_days": 10,
    "response_day_type": "calendar",
    "letter_prefix": "CPRA",
    "template": "foia_california.txt"
  },
  "texas": {
    "law_name": "Texas Public Information Act",
    "short_name": "TPIA",
    "citation": "Tex. Gov't Code Ch. 552",
    "fee_waiver_citation": "Tex. Gov't Code § 552.267",
    "exemption_citation": "Tex. Gov't Code Ch. 552, Subch. C",
    "response_days": 10,
    "response_day_type": "business",
    "letter_prefix": "TPIA",
    "template": "foia_texas.txt"
  },
  "new_york": {
    "law_name": "Freedom of Information Law",
    "short_name": "FOIL",
    "citation": "N.Y. Pub. Off. Law §§ 84–90",
    "fee_waiver_citation": "N.Y. Pub. Off. Law § 87(1)(c)",
    "exemption_citation": "N.Y. Pub. Off. Law § 87(2)",
    "response_days": 5,
    "response_day_type": "business",
    "letter_prefix": "FOIL",
    "template": "foia_new_york.txt"
  },
  "india": {
    "law_name": "Right to Information Act, 2005",
    "short_name": "RTI",
    "citation": "RTI Act, 2005 (Act No. 22 of 2005)",
    "fee_waiver_citation": "Section 7(5) of the RTI Act, 2005",
    "exemption_citation": "Section 8 of the RTI Act, 2005",
    "response_days": 30,
    "response_day_type": "calendar",
    "letter_prefix": "RTI",
    "template": "rti_india.txt",
    "application_fee": "10",
    "application_fee_currency": "INR"
  }
}
```

#### generator.py requirements:
- Load agencies.json and statutes.json
- Generate request_id as `f"{prefix}-{year}-{str(uuid.uuid4())[:8].upper()}"`
- Calculate response_due by adding response_days to today's date (skip weekends if business days)
- Use Jinja2 to render the correct template
- Return (letter_text, request_id, response_due)

#### tracker.py requirements:
- `init_db()` — creates requests.db with this schema:
```sql
CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    agency_key TEXT, agency_name TEXT, jurisdiction TEXT,
    subject TEXT, requester_name TEXT,
    date_sent TEXT, response_due TEXT,
    status TEXT DEFAULT 'SENT',
    output_file TEXT, n8n_notified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```
- `save_request(id, agency_key, agency_name, jurisdiction, subject, requester_name, date_sent, response_due, output_file)` — INSERT row
- `list_requests()` — SELECT all, return list of dicts
- `update_status(request_id, new_status)` — UPDATE status

#### main.py requirements:
- Use Click library
- Commands: `generate` (default), `--list`, `--list-agencies`, `--update-status`
- `--agency` option (required or prompted)
- `--jurisdiction` option (required or prompted), choices: federal, california, texas, new_york, india
- `--records` option (required or prompted)
- `--name` option (required or prompted)
- `--pdf` flag (optional)
- After generation, call `trigger_n8n()` wrapped in try/except
- Print coloured output using click.style():
  - Green for success lines
  - Yellow for in-progress
  - Red for errors
  - Blue for section headers
- Show letter preview (first 800 chars) after generation

#### n8n webhook function (inside main.py or separate n8n_client.py):
```python
import requests as req
import os

def trigger_n8n(payload: dict):
    url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/foia-request")
    enabled = os.getenv("N8N_ENABLED", "true").lower() == "true"
    if not enabled:
        return
    try:
        resp = req.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            click.echo(click.style("  ✓  n8n notified → webhook triggered", fg="magenta"))
        else:
            click.echo(click.style(f"  ⚠  n8n warning → HTTP {resp.status_code}", fg="yellow"))
    except Exception:
        click.echo(click.style("  ⚠  n8n offline → skipped (letter still saved)", fg="yellow"))
```

#### demo.py requirements:
Run these 5 requests in sequence, printing progress for each:
```python
DEMO_REQUESTS = [
    {"agency": "USDA",         "jurisdiction": "federal",    "records": "All inspection reports, non-compliance records, and enforcement actions for federally inspected slaughterhouses in Iowa for the period January 1, 2023 through December 31, 2024", "name": "Demo Requester"},
    {"agency": "FDA",          "jurisdiction": "federal",    "records": "All pesticide residue monitoring program test results, surveillance reports, import alerts, and refusal-of-admission records concerning pesticide residues on imported fresh produce for fiscal years 2022, 2023, and 2024", "name": "Demo Requester"},
    {"agency": "CA_CDFA",      "jurisdiction": "california", "records": "All dairy farm inspection reports, notices of violation, and corrective action orders for dairy operations in Fresno County, California for the period January 1, 2023 through December 31, 2024", "name": "Demo Requester"},
    {"agency": "TX_DSHS",      "jurisdiction": "texas",      "records": "All foodborne illness outbreak investigation reports, epidemiological summaries, laboratory confirmation records, and correspondence with the CDC related to outbreaks investigated by the DSHS Consumer Protection Division in Texas from January 1, 2023 through December 31, 2024", "name": "Demo Requester"},
    {"agency": "India_MoAFW",  "jurisdiction": "india",      "records": "All registration certificates, technical evaluation reports, and correspondence between the Central Insecticides Board and Registration Committee (CIB&RC) and applicant companies for pesticides approved under the Insecticides Act, 1968 during the period April 1, 2020 to March 31, 2024", "name": "Demo Requester"},
]
```

#### Jinja2 templates:
Each template must use these variables:
`{{ request_id }}`, `{{ date }}`, `{{ agency_officer }}`, `{{ agency_full_name }}`,
`{{ agency_address }}`, `{{ agency_city_state_zip }}`, `{{ agency_email }}`,
`{{ law_name }}`, `{{ citation }}`, `{{ fee_waiver_citation }}`, `{{ exemption_citation }}`,
`{{ records_description }}`, `{{ response_days }}`, `{{ response_day_type }}`,
`{{ response_due }}`, `{{ requester_name }}`

Write complete, realistic, formal letter templates for each jurisdiction.
The India RTI template must also include the ₹10 application fee statement.

#### pdf_export.py requirements:
- Use reportlab to generate a PDF
- Include: request ID header, date, agency address block, RE: line, full letter body
- Font: Helvetica, size 11, line spacing 14
- Page: A4, 72pt margins
- Function signature: `generate_pdf(letter_text: str, request_id: str, output_path: str)`

#### requirements.txt:
```
click==8.1.7
jinja2==3.1.2
requests==2.31.0
reportlab==4.1.0
python-dotenv==1.0.0
```

---

### Output format rules
- Print every file with a clear header comment showing filename
- All files must be complete and runnable — no `# TODO` or `pass` statements
- Python files must follow PEP8
- JSON files must be valid JSON
- Templates must produce zero unfilled `{{ }}` placeholders when rendered

---

## PROMPT END
