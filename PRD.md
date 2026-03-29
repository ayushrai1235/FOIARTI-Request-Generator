# Product Requirements Document (PRD)
## FOIA/RTI Request Generator CLI Tool
**Version:** 1.0.0  
**Date:** March 2025  
**Status:** Ready for Development

---

## 1. Product Overview

### 1.1 Purpose
A command-line tool that enables advocacy organizations, journalists, and citizens to automatically generate legally formatted Freedom of Information Act (FOIA) and Right to Information (RTI) request letters. Each letter includes correct legal citations, verified agency contact details, fee waiver justifications, and a tracking system for managing request lifecycles.

### 1.2 Problem Statement
Advocacy organizations file hundreds of public records requests against agriculture departments, slaughterhouses, and regulatory agencies. Each request requires:
- The correct statute and sub-section citation per jurisdiction
- The exact mailing address and email of the agency's FOIA/RTI office
- A legally appropriate fee waiver justification paragraph
- A system to track request status, deadlines, and follow-ups

Currently this is done manually, which is error-prone, slow, and non-scalable.

### 1.3 Solution
A Python CLI tool that takes three inputs — agency name, jurisdiction, and records description — and produces a complete, properly formatted request letter with all required legal language, plus automated dispatch and tracking via n8n workflows.

---

## 2. Target Users

| User Type | Description |
|---|---|
| Advocacy organizations | NGOs filing bulk records requests against agriculture/food regulators |
| Investigative journalists | Reporters seeking government documents for stories |
| Legal researchers | Law students and lawyers researching regulatory compliance |
| Citizens | Individuals exercising their right to access government records |

---

## 3. Jurisdictions Supported

| Jurisdiction | Law | Citation | Response Deadline |
|---|---|---|---|
| US Federal | Freedom of Information Act | 5 U.S.C. § 552 | 20 business days |
| California | California Public Records Act | Cal. Gov. Code § 7920 et seq. | 10 calendar days |
| Texas | Texas Public Information Act | Tex. Gov't Code Ch. 552 | 10 business days |
| New York | Freedom of Information Law | N.Y. Pub. Off. Law §§ 84–90 | 5 business days |
| India | Right to Information Act 2005 | RTI Act, 2005 (Act No. 22) | 30 days |

---

## 4. Agencies Supported (Demo Set)

| Key | Full Name | Jurisdiction | FOIA Email |
|---|---|---|---|
| USDA | U.S. Department of Agriculture | Federal | ams.foia@usda.gov |
| FDA | U.S. Food & Drug Administration | Federal | fdafoia@fda.hhs.gov |
| CA_CDFA | California Dept. of Food & Agriculture | California | publicrecords@cdfa.ca.gov |
| TX_DSHS | Texas Dept. of State Health Services | Texas | dshs.openrecords@dshs.texas.gov |
| India_MoAFW | Ministry of Agriculture & Farmers Welfare | India | RTI cell, Krishi Bhawan |

---

## 5. Core Features

### F1 — Letter Generation
- Accept agency, jurisdiction, records description, and requester name as inputs
- Load agency details from `agencies.json`
- Load statute details from `statutes.json`
- Render Jinja2 template with all fields populated
- Output a complete, print-ready letter

### F2 — Legal Citations
- Automatically insert the correct primary statute citation
- Insert the correct fee waiver sub-section citation
- Include response deadline based on jurisdiction
- Include correct exemption reference language

### F3 — Fee Waiver Paragraph
- Auto-generate a jurisdiction-appropriate fee waiver paragraph
- Cite the correct statutory basis for the waiver
- State public interest justification
- State non-commercial nature of the request

### F4 — Tracking System
- Generate a unique request ID per letter (format: `{LAW_PREFIX}-{YEAR}-{8CHAR_UUID}`)
- Save metadata to SQLite database (`requests.db`)
- Track: ID, agency, jurisdiction, subject, date sent, response deadline, status
- Status values: SENT, RESPONDED, OVERDUE, CLOSED
- `--list` command to display all tracked requests in a table

### F5 — Output Files
- Save letter as `.txt` file in `output/` directory
- Filename = request ID (e.g., `FOIA-2025-A7F3C2D1.txt`)
- Optional `--pdf` flag to also generate a PDF via reportlab

### F6 — n8n Integration
- After generation, POST a webhook to n8n with full request payload
- n8n workflow handles: email dispatch, Google Sheets logging, follow-up scheduling
- Graceful fallback if n8n is offline (tool still works fully without it)

### F7 — Demo Mode
- `python demo.py` runs all 5 pre-configured requests automatically
- Generates all 5 letters and saves them
- Logs all 5 to tracking database
- Triggers all 5 n8n webhooks

### F8 — Validation & Error Handling
- Validate agency key exists in `agencies.json`
- Validate jurisdiction is one of 5 supported values
- Show helpful error messages with list of valid options
- Handle n8n webhook failure silently with a warning

### F9 — CLI Interface
- Both flag mode: `python main.py --agency USDA --jurisdiction federal ...`
- And interactive prompt mode: `python main.py` (prompts user for each field)
- `--list` to show tracking table
- `--list-agencies` to show all supported agencies
- `--status` to update a request status by ID

---

## 6. Non-Functional Requirements

| Requirement | Specification |
|---|---|
| Language | Python 3.9+ |
| Response time | Letter generated in under 2 seconds |
| Offline capability | Must work without internet / n8n |
| Platform | macOS, Linux, Windows (WSL) |
| Data storage | Local SQLite — no cloud dependency for core features |

---

## 7. Out of Scope (v1.0)

- Web UI or browser interface
- Multiple laws per jurisdiction (single primary statute per jurisdiction)
- Automatic receipt of government responses
- Integration with FOIA online portals (e.g., foiamachine.org)
- Authentication or multi-user support

---

## 8. Success Metrics

- 5 demo requests generated correctly with accurate legal citations
- All 5 jurisdictions produce letters with correct statute citations
- Fee waiver paragraph present in every letter
- Tracking IDs generated and stored for all requests
- n8n workflow successfully emails and logs at least 1 request end-to-end
