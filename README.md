# FOIA/RTI Request Generator

> A production-quality Python CLI tool that generates legally formatted Freedom of Information Act (FOIA) and Right to Information (RTI) request letters with automated tracking and n8n workflow integration.

## ✨ Features

- **5 Jurisdictions Supported**: US Federal (FOIA), California (CPRA), Texas (TPIA), New York (FOIL), India (RTI)
- **Legally Correct Letters**: Proper statute citations, fee waiver paragraphs, response deadlines, and exemption clauses
- **Request Tracking**: PostgreSQL database (Neon) with status tracking (SENT / RESPONDED / OVERDUE / CLOSED)
- **PDF Export**: Optional PDF generation using ReportLab
- **n8n Integration**: Automated webhook dispatch for email sending, Google Sheets logging, and follow-up scheduling
- **Demo Mode**: Run 5 pre-configured requests across all jurisdictions instantly
- **Clean CLI UX**: Colored output, interactive prompts, formatted tables

## 📋 Prerequisites

- Python 3.9+
- [Neon](https://neon.tech) PostgreSQL database (free tier available)
- n8n (optional, for automation workflows)

## 🚀 Quick Start

### 1. Clone and install

```bash
git clone <repository-url>
cd foia-rti-tool
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Neon DATABASE_URL and n8n webhook URL
```

Your `.env` file should contain:

```env
DATABASE_URL=postgresql://neondb_owner:your_password@your-host.neon.tech/neondb?sslmode=require
N8N_WEBHOOK_URL=http://localhost:5678/webhook/foia-request
N8N_ENABLED=true
REQUESTER_DEFAULT_NAME=Your Name
REQUESTER_DEFAULT_EMAIL=your@email.com
```

### 3. Run the demo

```bash
python demo.py
```

This generates 5 sample requests across all jurisdictions, saves them to `output/`, tracks them in the database, and triggers n8n webhooks.

## 📖 Usage

### Generate a request (flag mode)

```bash
python main.py \
  --agency USDA \
  --jurisdiction federal \
  --records "slaughterhouse inspection reports Iowa 2023-2024" \
  --name "Jane Doe"
```

### Generate a request (interactive mode)

```bash
python main.py
# Follow the prompts for agency, jurisdiction, records, and name
```

### Generate with PDF

```bash
python main.py \
  --agency USDA \
  --jurisdiction federal \
  --records "inspection reports" \
  --name "Jane Doe" \
  --pdf
```

### List tracked requests

```bash
python main.py --list
```

### List available agencies

```bash
python main.py --list-agencies
```

### Update request status

```bash
python main.py --update-status --id FOIA-2025-A7F3C2D1 --status RESPONDED
```

### Run demo mode

```bash
python main.py --demo
# or
python demo.py
```

## 🏗️ Project Structure

```
foia-rti-tool/
├── main.py                  ← Click CLI entry point
├── generator.py             ← Letter generation logic
├── tracker.py               ← PostgreSQL (Neon) tracking
├── demo.py                  ← Runs 5 demo requests
├── pdf_export.py            ← PDF generation (ReportLab)
├── n8n_client.py            ← n8n webhook client
│
├── agencies.json            ← Agency contact data (5 agencies)
├── statutes.json            ← Statute citations (5 jurisdictions)
│
├── templates/
│   ├── foia_federal.txt     ← Federal FOIA template
│   ├── foia_california.txt  ← California CPRA template
│   ├── foia_texas.txt       ← Texas TPIA template
│   ├── foia_new_york.txt    ← New York FOIL template
│   └── rti_india.txt        ← India RTI template
│
├── output/                  ← Generated letters (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

## 📊 Supported Agencies

| Key | Full Name | Jurisdiction |
|---|---|---|
| USDA | U.S. Department of Agriculture | Federal |
| FDA | U.S. Food and Drug Administration | Federal |
| CA_CDFA | California Dept. of Food & Agriculture | California |
| TX_DSHS | Texas Dept. of State Health Services | Texas |
| India_MoAFW | Ministry of Agriculture & Farmers Welfare | India |

## ⚖️ Jurisdictions & Statutes

| Jurisdiction | Law | Citation | Response Deadline |
|---|---|---|---|
| Federal | Freedom of Information Act | 5 U.S.C. § 552 | 20 business days |
| California | California Public Records Act | Cal. Gov. Code § 7920 et seq. | 10 calendar days |
| Texas | Texas Public Information Act | Tex. Gov't Code Ch. 552 | 10 business days |
| New York | Freedom of Information Law | N.Y. Pub. Off. Law §§ 84–90 | 5 business days |
| India | Right to Information Act 2005 | RTI Act, 2005 (Act No. 22) | 30 calendar days |

## 🔗 n8n Integration

The tool triggers an n8n webhook after each letter is generated. The webhook payload includes:

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

n8n workflows handle:
1. **Request Dispatch** — Emails the letter to the agency, logs to Google Sheets, confirms to requester
2. **Follow-up Scheduler** — Daily check for overdue requests, sends follow-up emails

> **Note:** n8n is optional. The tool works fully offline — if n8n is unreachable, a warning is shown but the letter is still saved.

## 🗄️ Database

The application uses **Neon PostgreSQL** for request tracking. The schema:

| Field | Type | Description |
|---|---|---|
| id | TEXT PK | Unique request ID (e.g., FOIA-2025-A7F3C2D1) |
| agency_key | TEXT | Agency shortcode |
| agency_name | TEXT | Full agency name |
| jurisdiction | TEXT | Jurisdiction key |
| subject | TEXT | First 100 chars of description |
| requester_name | TEXT | Requester's name |
| date_sent | TEXT | ISO date |
| response_due | TEXT | Calculated deadline |
| status | TEXT | SENT / RESPONDED / OVERDUE / CLOSED |
| output_file | TEXT | Path to saved letter |
| n8n_notified | INTEGER | 0 or 1 |
| created_at | TIMESTAMPTZ | Auto-generated timestamp |

## 📜 License

MIT License

## 👤 Author

Built for advocacy organizations, investigative journalists, legal researchers, and citizens exercising their right to access government records.
