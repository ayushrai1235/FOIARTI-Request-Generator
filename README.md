# FOIA/RTI Request Generator Dashboard & Workflow

> A powerful, full-stack application that automatically generates legally formatted Freedom of Information Act (FOIA) and Right to Information (RTI) request letters, dispatches them, tracks responses, and schedules automated follow-ups.

## 📖 The Story & Development Approach

### Phase 1: The CLI Foundation
The project initially began as a **Command Line Interface (CLI)** tool written purely in Python. The goal was simple: journalists, activists, and citizens shouldn’t need a law degree to draft a legally binding FOIA or RTI request. The CLI tool took a user's description, parsed local statutes, calculated legal deadlines, formatted a formal letter using specific templates, and saved them as text or PDF files while logging the entry into a database.

### Phase 2: Mentor Feedback & The Pivot to a Full-Stack UI
After building the functional but technical CLI, I presented the progress to my mentor. The feedback was invaluable: *“The logic is incredibly powerful, but to truly democratize access to public records, this needs to be accessible to non-technical users through a visual interface.”*

Encouraged by this, the project was completely restructured. The core Python logic was abstracted into a robust **FastAPI Backend**, and a modern, beautiful **React Frontend** was built on top of it. 

The approach shifted from a developer tool to a fully integrated **FOIARTI Workspace** that provides an end-to-end user experience—from selecting the agency in a sleek dropdown to tracking the overdue status of pending requests visually. Finally, **n8n** was integrated to handle all the heavy lifting of emailing agencies, logging to Google Sheets, and checking for overdue timelines without blocking the web backend.

---

## ✨ Comprehensive Feature Breakdown

### 1. Multi-Jurisdictional Legal Logic Engine
The core of the system is its legal awareness. It currently supports **5 distinct jurisdictions**:
- **US Federal (FOIA)**: 5 U.S.C. § 552 (20 business days)
- **California (CPRA)**: Cal. Gov. Code § 7920 et seq. (10 calendar days)
- **Texas (TPIA)**: Tex. Gov't Code Ch. 552 (10 business days)
- **New York (FOIL)**: N.Y. Pub. Off. Law §§ 84–90 (5 business days)
- **India (RTI)**: RTI Act, 2005 (30 calendar days)

Selecting an agency automatically triggers the correct legal citations, formats the letter structure (including fee waivers and exemption parameters), and calculates the precise legal deadline for the agency to respond based on the state or federal statute.

### 2. Interactive Request Dashboard (React + Tailwind)
A modern, glassmorphic UI built with React. It features:
- **Guided Form**: Select agencies, view live statute summaries, and enter request descriptions mapping to the specific law.
- **Demo Mode**: A single click that generates 5 complex sample requests across varying jurisdictions automatically, verifying the database logic and workflow connection instantly.
- **Active Tracking Table**: A live data table mapping all requests, highlighting statuses through color-coded badges (`SENT`, `OVERDUE`, `RESPONDED`, `CLOSED`, `FOLLOWED_UP`).

### 3. n8n Full Automation Integration
The system doesn't just generate a document locally; the FastAPI backend pushes a webhook to an `n8n` workflow containing the full legal letter, the agency email, and the deadline.
- **Automated Dispatch**: n8n sends the email directly to the government agency.
- **Sender Transparency**: The `replyTo` and `senderName` headers are dynamically populated with the frontend user's exact details. Any reply from the agency is addressed directly to the citizen who filled out the form.
- **Confirmation Notifications**: Sends a receipt email directly to the requester confirming transmission and providing a timeline.
- **Google Sheets Logging**: Automatically backs up all raw requests and their statuses into a shared tracking sheet.

### 4. Automated Daily Scheduler & Follow-Ups
Also built into the `n8n` workflow is an autonomous cron-trigger that evaluates the Google Sheets database daily at **9:00 AM**.
- If a request's legal deadline has passed by 30 days and the status remains pending, the system automatically drafts and dispatches a firm, professional legal follow-up pointing out the expired statutory limits and demanding an immediate response. 
- The React UI contains a dedicated component highlighting that this scheduler is active, providing clarity to the user.

### 5. Excel Mass Export
For journalists and historical researchers handling hundreds of requests, the system features a dedicated `/api/export/excel` endpoint powered by `pandas` and `openpyxl`. 
With a single click within the dashboard, users can download a perfectly formatted, auto-column-width-adjusted `.xlsx` Master Tracker containing all historical request data tracked in the database.

### 6. PDF Generation Support
Users can optionally toggle a capability to convert the dynamically generated letters into official, cleanly formatted `.pdf` documents directly on the backend before the request is officially dispatched to the agency.

---

## 🚀 How to Run Locally

Follow these precise steps to get the full stack (Frontend, Backend, and Automation) running on your local machine.

### Prerequisites
- [Node.js](https://nodejs.org/) (v16+)
- [Python](https://www.python.org/) (3.9+)
- [n8n](https://n8n.io/) (Run via Docker, desktop app, or `npm install -g n8n`)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "FOIARTI Request Generator"
```

### Step 2: Configure the Backend (FastAPI)
The backend manages the database, generation formatting, formatting, and the REST API endpoints.
```bash
cd backend

# Create a virtual environment (Recommended)
python -m venv venv
# Activate it
# macOS/Linux: source venv/bin/activate
# Windows: venv\Scripts\activate

# Install Python requirements
pip install -r requirements.txt

# Create your environmental variables from the example
cp .env.example .env
```
Inside your new `.env` file, ensure you properly map the database tracking method and webhook target:
```env
# Example .env configuration
DATABASE_URL=sqlite:///./foia_tracker.db
N8N_WEBHOOK_URL=http://localhost:5678/webhook/foia-request
```
*Start up the backend server:*
```bash
python -m uvicorn api:app --reload --port 8000
```
*Your API is now available and listening at `http://localhost:8000`.*

### Step 3: Configure the Frontend (React / Vite)
Open a brand new terminal window inside the root project directory.
```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
*The React UI is now accessible in your browser at `http://localhost:5173`.*

### Step 4: Import and Configure the n8n Workflow
To handle all external automation (emails, spreadsheets, scheduling):
1. Start your local n8n instance (e.g., executing `n8n start` from a new terminal).
2. Navigate to your n8n dashboard (usually `http://localhost:5678`).
3. Click to create a **New Workflow**.
4. In the top right corner of the canvas, click the **Options menu (three dots) > Import from File**.
5. Select the included `FOIA_RTI Request Generator — Complete Workflow.json` file from the root of the project.
6. Connect your **Google (Gmail)** and **Google Sheets** OAuth2 credentials inside the two respective nodes. *Note: n8n handles the heavy lifting of OAuth flow for you under the "Credentials" tab.*
7. Ensure your Test Google Sheet contains the appropriate headers (`Request ID`, `Agency Name`, `Agency Email`, `Agency Key`, `Jurisdiction`, `Subject`, `Requester Name`, `Date Sent`, `Response Due`, `Status`, `Output File`).
8. Click **Activate** at the top right of the canvas to turn on the webhook listener and the 9:00 AM daily scheduler.

### Step 5: Test the Application!
1. Open the Frontend UI at `http://localhost:5173`.
2. Select your target agency (e.g. "U.S. Department of Agriculture").
3. Enter a mock request description, your name, and your real email address.
4. Click **Dispatch Request**.
5. **Observe:** The FastAPI backend will parse the legal logic, save to the local SQLite database, and fire a payload to the n8n webhook.
6. **Observe:** Check n8n; you can watch the execution flow light up in real-time as it sends the email and logs it simultaneously to Google Sheets!
7. **Observe:** Click **Export to Excel** on the dashboard to test the `pandas` export utility downloading your live database tracking `.xlsx` file.

---

## 🏗️ Project Structure

The repository is modularly split into a FastAPI Backend and a React Frontend, with an external JSON blob handling the n8n logic.

```text
foia-rti-tool/
├── backend/                             ← Python/FastAPI Core Logic
│   ├── api.py                           ← RESTful endpoints
│   ├── generator.py                     ← Legal letter formatting engine
│   ├── tracker.py                       ← SQLite / PostgreSQL tracking logic
│   ├── demo.py                          ← One-click demo generation logic
│   ├── n8n_client.py                    ← Webhook transmission utility
│   ├── pdf_export.py                    ← ReportLab PDF generator
│   ├── agencies.json                    ← Extensible database of Govt Entities
│   ├── statutes.json                    ← Legal reference and deadline metadata
│   ├── templates/                       ← .txt templates per jurisdiction
│   └── requirements.txt                 ← Python dependencies
│
├── frontend/                            ← React/Vite Dashboard
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── App.tsx                      ← Primary Interactive App Component
│       ├── main.tsx
│       └── index.css                    ← Tailwind utilities/variables
│
├── FOIA_RTI Request Generator...json    ← The n8n importable workflow
├── example_requests.md                  ← Sample prompts to test with
└── README.md
```

---

## ⚖️ Jurisdictions Covered

| Jurisdiction | Law | Statute Citation | Response Deadline |
|---|---|---|---|
| Federal | Freedom of Information Act | 5 U.S.C. § 552 | 20 business days |
| California | California Public Records Act | Cal. Gov. Code § 7920 et seq. | 10 calendar days |
| Texas | Texas Public Information Act | Tex. Gov't Code Ch. 552 | 10 business days |
| New York | Freedom of Information Law | N.Y. Pub. Off. Law §§ 84–90 | 5 business days |
| India | Right to Information Act 2005 | RTI Act, 2005 (Act No. 22) | 30 calendar days |

## 📜 License
MIT License

## 👤 Author & Audience
Built to empower advocacy organizations, investigative journalists, legal researchers, and citizens exercising their fundamental right to access government records.
