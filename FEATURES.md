# Features & Acceptance Criteria
## FOIA/RTI Request Generator CLI Tool
**Version:** 1.0.0

---

## Feature 1 — CLI Entry Point

**Command:** `python main.py`

### Flag mode
```bash
python main.py \
  --agency USDA \
  --jurisdiction federal \
  --records "slaughterhouse inspection reports Iowa 2023-2024" \
  --name "Jane Doe"
```

### Interactive mode (no flags)
```bash
python main.py
# Prompts: Agency name > Jurisdiction > Records description > Your name
```

### Other commands
```bash
python main.py --list                          # show tracking table
python main.py --list-agencies                 # show all valid agency keys
python main.py --update-status --id FOIA-2025-XXXX --status RESPONDED
python main.py --agency USDA --jurisdiction federal --records "..." --name "..." --pdf
```

**Acceptance criteria:**
- [ ] Both flag and interactive modes work
- [ ] `--list` shows a formatted table from SQLite
- [ ] `--list-agencies` shows all keys from agencies.json
- [ ] Invalid agency shows helpful error + valid options
- [ ] Invalid jurisdiction shows helpful error + valid options
- [ ] `--pdf` generates a PDF in addition to .txt

---

## Feature 2 — Letter Generation

**File:** `generator.py`

Each generated letter must contain:

1. Request ID and date at the top
2. Agency officer title, full agency name, address, email
3. RE: line summarising the records sought
4. Opening paragraph citing the correct statute and citation
5. Records description paragraph (verbatim from user input)
6. Fee waiver paragraph citing correct sub-section
7. Response deadline statement citing correct number of days
8. Exemption notice (if withholding, cite correct exemption section)
9. Requester name and contact block at the bottom

**Acceptance criteria:**
- [ ] Federal letters cite `5 U.S.C. § 552`
- [ ] California letters cite `Cal. Gov. Code § 7920 et seq.`
- [ ] Texas letters cite `Tex. Gov't Code Ch. 552`
- [ ] New York letters cite `N.Y. Pub. Off. Law §§ 84–90`
- [ ] India letters cite `RTI Act, 2005 (Act No. 22 of 2005)`
- [ ] Every letter has a fee waiver paragraph
- [ ] Every letter states the correct response deadline
- [ ] Letter renders fully — no unfilled `{{ }}` placeholders

---

## Feature 3 — Fee Waiver Paragraph

Auto-generated in every letter. Must include:

- The statutory basis for the waiver (correct sub-section per jurisdiction)
- A public interest statement
- A non-commercial purpose statement

**Federal example:**
> Pursuant to 5 U.S.C. § 552(a)(4)(A)(iii), I request a full fee waiver on the grounds that disclosure of this information is in the public interest because it is likely to contribute significantly to public understanding of the operations or activities of the government and is not primarily in my commercial interest.

**Acceptance criteria:**
- [ ] Fee waiver paragraph present in all 5 jurisdictions
- [ ] Correct sub-section cited per jurisdiction
- [ ] Public interest language present
- [ ] Non-commercial language present

---

## Feature 4 — Tracking System

**File:** `tracker.py` + `requests.db`

### Request ID format
```
{LAW_PREFIX}-{YEAR}-{8_CHAR_UUID_UPPERCASE}

Examples:
  FOIA-2025-A7F3C2D1   (federal)
  CPRA-2025-B8E4D9F2   (california)
  TPIA-2025-C1A5B7E3   (texas)
  FOIL-2025-D9F2C4A8   (new york)
  RTI-2025-E3B6D1C9    (india)
```

### Tracked fields
| Field | Type | Description |
|---|---|---|
| id | TEXT PK | Unique request ID |
| agency_key | TEXT | e.g. USDA |
| agency_name | TEXT | Full agency name |
| jurisdiction | TEXT | e.g. federal |
| subject | TEXT | First 100 chars of records description |
| requester_name | TEXT | Name of requester |
| date_sent | TEXT | ISO date YYYY-MM-DD |
| response_due | TEXT | ISO date, calculated from deadline |
| status | TEXT | SENT / RESPONDED / OVERDUE / CLOSED |
| output_file | TEXT | Path to saved .txt file |
| n8n_notified | INTEGER | 0 or 1 |

### `--list` output format
```
──────────────────────────────────────────────────────────────────────
ID                    AGENCY        JURISDICTION  DATE        STATUS
──────────────────────────────────────────────────────────────────────
FOIA-2025-A7F3C2D1    USDA          Federal       2025-01-15  SENT
CPRA-2025-B8E4D9F2    CA CDFA       California    2025-01-17  RESPONDED
RTI-2025-E3B6D1C9     India MoAFW   India RTI     2025-01-19  OVERDUE
──────────────────────────────────────────────────────────────────────
Total: 3   Sent: 1   Responded: 1   Overdue: 1
```

**Acceptance criteria:**
- [ ] Unique ID generated for every request
- [ ] ID prefix matches jurisdiction law
- [ ] Response due date correctly calculated
- [ ] `--list` shows formatted table with status colours
- [ ] `--update-status` correctly updates the SQLite row

---

## Feature 5 — Output Files

**Directory:** `output/`

- `.txt` file created for every request
- Filename = request ID
- `output/` directory auto-created if not present
- Optional PDF output with `--pdf` flag

**Acceptance criteria:**
- [ ] `output/FOIA-2025-XXXXXXXX.txt` created on every run
- [ ] File contains the full rendered letter
- [ ] `output/` auto-created if missing
- [ ] `--pdf` creates `output/FOIA-2025-XXXXXXXX.pdf` alongside the .txt

---

## Feature 6 — n8n Integration

**Trigger:** POST to `N8N_WEBHOOK_URL` after letter is generated

### Workflow 1 — Request dispatch
Triggered by webhook. Does:
1. Sends the generated letter as email body to `agency_email`
2. Appends a row to Google Sheets tracking spreadsheet
3. Sends a confirmation email to the requester

### Workflow 2 — Follow-up scheduler
Runs daily. Does:
1. Reads Google Sheets for rows with status = SENT
2. Checks if `date_sent + 30 days <= today`
3. Sends a follow-up email to the agency
4. Updates the sheet row to FOLLOWED_UP

**Acceptance criteria:**
- [ ] Webhook fires after every successful generation
- [ ] n8n failure does not crash the Python tool
- [ ] Warning message shown if n8n is unreachable
- [ ] Agency receives email with full letter text
- [ ] Google Sheets row appended with correct metadata
- [ ] Follow-up email sent after 30 days automatically

---

## Feature 7 — Demo Mode

**File:** `demo.py`

Runs 5 pre-configured requests covering all 5 jurisdictions:

| # | Agency | Jurisdiction | Subject |
|---|---|---|---|
| 1 | USDA | Federal | Slaughterhouse inspection violation reports, Iowa, 2023–2024 |
| 2 | FDA | Federal | Pesticide residue test results on imported produce, 2022–2024 |
| 3 | CA_CDFA | California | Dairy farm inspection violations, Fresno County, 2023 |
| 4 | TX_DSHS | Texas | Foodborne illness outbreak investigation records, 2023 |
| 5 | India_MoAFW | India | Pesticide registration approval files, CIB&RC, 2020–2024 |

**Acceptance criteria:**
- [ ] All 5 letters generated without errors
- [ ] All 5 saved to `output/`
- [ ] All 5 logged to `requests.db`
- [ ] All 5 n8n webhooks fired (or gracefully skipped if offline)
- [ ] Summary printed at end: `5/5 requests generated successfully`

---

## Feature 8 — Validation & Error Handling

**Acceptance criteria:**
- [ ] Unknown agency → print error + list valid agency keys
- [ ] Unknown jurisdiction → print error + list valid jurisdictions
- [ ] n8n offline → print yellow warning, continue successfully
- [ ] Missing output/ dir → auto-create it
- [ ] Empty records description → prompt again / show error
- [ ] All error messages are human-readable, not stack traces

---

## Colour Coding (CLI output)

| Colour | Meaning |
|---|---|
| Green | Success (saved, tracked, sent) |
| Yellow | Warning or in-progress |
| Red | Error |
| Blue | Info / section header |
| Cyan/Purple | n8n status |
| White | Neutral data (agency name, address, etc.) |
