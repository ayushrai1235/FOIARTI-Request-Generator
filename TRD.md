# Technical Requirements Document (TRD)
## FOIA/RTI Request Generator CLI Tool
**Version:** 1.0.0  
**Date:** March 2025

---

## 1. Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.9+ | Core application |
| CLI Framework | Click | 8.x | Command-line interface |
| Templating | Jinja2 | 3.x | Letter template rendering |
| Database | SQLite (built-in) | — | Request tracking |
| PDF Generation | ReportLab | 4.x | Optional PDF output |
| HTTP Client | requests | 2.x | n8n webhook calls |
| Automation | n8n | latest | Email, sheets, reminders |
| Data Format | JSON | — | Agency and statute config |

---

## 2. Project Structure

```
foia-rti-tool/
│
├── main.py                  ← CLI entry point (Click commands)
├── generator.py             ← Letter generation logic
├── tracker.py               ← SQLite tracking logic
├── demo.py                  ← Runs all 5 demo requests
├── pdf_export.py            ← Optional PDF generation
│
├── agencies.json            ← Agency addresses, emails, FOIA officers
├── statutes.json            ← Laws, citations, deadlines per jurisdiction
│
├── templates/
│   ├── foia_federal.txt     ← Federal FOIA letter template
│   ├── foia_california.txt  ← California CPRA letter template
│   ├── foia_texas.txt       ← Texas TPIA letter template
│   ├── foia_new_york.txt    ← New York FOIL letter template
│   └── rti_india.txt        ← India RTI letter template
│
├── output/                  ← Generated letters saved here (auto-created)
├── requests.db              ← SQLite tracking database (auto-created)
├── requirements.txt
└── README.md
```

---

## 3. Data Schemas

### 3.1 agencies.json
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

### 3.2 statutes.json
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

### 3.3 SQLite Schema — requests table
```sql
CREATE TABLE IF NOT EXISTS requests (
    id              TEXT PRIMARY KEY,
    agency_key      TEXT NOT NULL,
    agency_name     TEXT NOT NULL,
    jurisdiction    TEXT NOT NULL,
    subject         TEXT NOT NULL,
    requester_name  TEXT NOT NULL,
    date_sent       TEXT NOT NULL,
    response_due    TEXT NOT NULL,
    status          TEXT DEFAULT 'SENT',
    output_file     TEXT,
    n8n_notified    INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Module Specifications

### 4.1 generator.py
```
Input:  agency_key, jurisdiction, records_description, requester_name
Output: (letter_text: str, request_id: str, response_due: str)

Steps:
1. Load agencies.json → get agency dict
2. Load statutes.json → get statute dict
3. Generate request_id = f"{prefix}-{year}-{uuid[:8].upper()}"
4. Calculate response_due from today + response_days
5. Load Jinja2 template for jurisdiction
6. Render template with all variables
7. Return rendered string + metadata
```

### 4.2 tracker.py
```
Functions:
- init_db()            → Creates requests.db and table if not exists
- save_request(...)    → INSERT row into requests table
- list_requests()      → SELECT all rows, return as list of dicts
- update_status(id, status) → UPDATE status by request ID
```

### 4.3 main.py (Click commands)
```
Commands:
- generate   (default)  → --agency --jurisdiction --records --name [--pdf]
- list                  → shows tracking table
- list-agencies         → shows all keys in agencies.json
- update-status         → --id --status
- demo                  → alias for running demo.py inline
```

### 4.4 n8n webhook payload
```json
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
```

---

## 5. Template Variables

All templates receive these Jinja2 variables:

| Variable | Example Value |
|---|---|
| `{{ request_id }}` | FOIA-2025-A7F3C2D1 |
| `{{ date }}` | January 15, 2025 |
| `{{ agency_officer }}` | FOIA Officer |
| `{{ agency_full_name }}` | U.S. Department of Agriculture |
| `{{ agency_address }}` | 1400 Independence Ave SW |
| `{{ agency_city_state_zip }}` | Washington, DC 20250 |
| `{{ agency_email }}` | ams.foia@usda.gov |
| `{{ law_name }}` | Freedom of Information Act |
| `{{ citation }}` | 5 U.S.C. § 552 |
| `{{ fee_waiver_citation }}` | 5 U.S.C. § 552(a)(4)(A)(iii) |
| `{{ exemption_citation }}` | 5 U.S.C. § 552(b) |
| `{{ records_description }}` | slaughterhouse inspection records Iowa 2023 |
| `{{ response_days }}` | 20 |
| `{{ response_day_type }}` | business |
| `{{ response_due }}` | February 14, 2025 |
| `{{ requester_name }}` | Jane Doe |

---

## 6. n8n Workflow Architecture

### Workflow 1 — Request Dispatch (triggered by webhook)
```
Webhook node (POST /webhook/foia-request)
  → Gmail / SMTP node     (send letter to agency_email)
  → Google Sheets node    (append row: id, agency, date, status=SENT)
  → Gmail notify node     (send confirmation to requester)
```

### Workflow 2 — Follow-up Scheduler (runs daily)
```
Schedule Trigger (daily at 9am)
  → Google Sheets node    (read all rows where status=SENT)
  → IF node               (filter rows where date_sent + 30 days <= today)
  → Gmail node            (send follow-up email to agency)
  → Google Sheets node    (update status to FOLLOWED_UP)
```

---

## 7. Error Handling

| Error | Behaviour |
|---|---|
| Unknown agency key | Print error + list valid keys, exit with code 1 |
| Unknown jurisdiction | Print error + list valid jurisdictions, exit with code 1 |
| Missing template file | Print error with template path, exit with code 1 |
| n8n webhook timeout | Print warning, continue — do not fail the request |
| n8n webhook 4xx/5xx | Print warning with status code, continue |
| SQLite write failure | Print error, letter still saved to output/ |

---

## 8. Dependencies — requirements.txt
```
click==8.1.7
jinja2==3.1.2
requests==2.31.0
reportlab==4.1.0
```

---

## 9. Environment Variables (.env)
```
N8N_WEBHOOK_URL=http://localhost:5678/webhook/foia-request
N8N_ENABLED=true
REQUESTER_DEFAULT_NAME=Your Name
REQUESTER_DEFAULT_EMAIL=your@email.com
```
