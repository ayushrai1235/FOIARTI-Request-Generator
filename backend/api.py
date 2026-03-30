import sys
from pathlib import Path
from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io

from generator import generate_letter, load_agencies
from n8n_client import trigger_n8n
from pdf_export import generate_pdf
from tracker import init_db, list_requests, save_request, update_status, mark_n8n_notified
from demo import DEMO_REQUESTS

BASE_DIR = Path(__file__).resolve().parent
output_dir = BASE_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="FOIARTI Request Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

class GenerateRequest(BaseModel):
    agency: str
    jurisdiction: str
    records: str
    name: str
    email: str
    pdf: bool = False

class StatusUpdate(BaseModel):
    status: str

@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    agencies = load_agencies()
    if req.agency not in agencies:
        raise HTTPException(status_code=400, detail=f"Unknown agency: {req.agency}")
        
    agency_data = agencies[req.agency]
    
    try:
        letter_text, req_id, response_due = generate_letter(
            agency_key=req.agency,
            jurisdiction=req.jurisdiction.lower(),
            records_description=req.records,
            requester_name=req.name,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    txt_path = output_dir / f"{req_id}.txt"
    txt_path.write_text(letter_text, encoding="utf-8")
    
    pdf_path = None
    if req.pdf:
        pdf_path = output_dir / f"{req_id}.pdf"
        try:
            generate_pdf(letter_text, req_id, str(pdf_path))
        except Exception as e:
            print(f"PDF generation failed: {e}")
            
    # Save to tracker
    try:
        save_request(
            request_id=req_id,
            agency_key=req.agency,
            agency_name=agency_data["full_name"],
            jurisdiction=req.jurisdiction.lower(),
            subject=req.records[:100],
            requester_name=req.name,
            date_sent=date.today().isoformat(),
            response_due=response_due,
            output_file=str(txt_path)
        )
    except Exception as e:
        print(f"Tracking failed: {e}")
        
    # Trigger n8n
    n8n_payload = {
        "request_id": req_id,
        "agency_name": agency_data["full_name"],
        "agency_email": agency_data["foia_email"],
        "jurisdiction": req.jurisdiction.lower(),
        "subject": req.records[:100],
        "requester_name": req.name,
        "user_email": req.email, # INJECT EMAIL HERE AS REQUESTED
        "date_sent": date.today().isoformat(),
        "response_due": response_due,
        "letter_text": letter_text,
        "output_file": str(txt_path),
    }
    
    if trigger_n8n(n8n_payload):
        try:
            mark_n8n_notified(req_id)
        except Exception:
            pass
            
    return {
        "id": req_id,
        "message": "Request generated successfully",
        "response_due": response_due
    }

@app.get("/api/requests")
def get_requests():
    return list_requests()

import json

@app.get("/api/config")
def get_config():
    agencies = load_agencies()
    statutes_path = BASE_DIR / "statutes.json"
    statutes = {}
    if statutes_path.exists():
        statutes = json.loads(statutes_path.read_text(encoding="utf-8"))
    return {"agencies": agencies, "statutes": statutes}

@app.patch("/api/status/{req_id}")
def api_update_status(req_id: str, payload: StatusUpdate):
    try:
        updated = update_status(req_id, payload.status)
        if not updated:
            raise HTTPException(status_code=404, detail="Request not found")
        return {"id": req_id, "status": payload.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export/excel")
def export_excel():
    requests = list_requests()
    if not requests:
        df = pd.DataFrame(columns=["Request ID", "Agency", "Jurisdiction", "Date Sent", "Response Due", "Status"])
    else:
        # Create a nice layout formatting for the excel document
        df = pd.DataFrame(requests)
        # Rename columns for clarity
        df.rename(columns={
            "id": "Request ID",
            "agency_name": "Agency",
            "jurisdiction": "Jurisdiction",
            "subject": "Subject",
            "requester_name": "Requester Name",
            "date_sent": "Date Sent",
            "response_due": "Response Due",
            "status": "Status",
            "n8n_notified": "n8n Triggered"
        }, inplace=True)
        # Keep only relevant columns for the export
        columns_to_keep = ["Request ID", "Agency", "Jurisdiction", "Subject", "Requester Name", "Date Sent", "Response Due", "Status", "n8n Triggered"]
        df = df[[col for col in columns_to_keep if col in df.columns]]
        
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='FOIA Requests Tracker')
        # Auto-adjust columns
        worksheet = writer.sheets['FOIA Requests Tracker']
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter # Get the column name
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = min(adjusted_width, 50)
            
    output.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename="FOIAMasterTracker.xlsx"'
    }
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.post("/api/demo")
def api_demo():
    agencies = load_agencies()
    results = []
    
    for req_data in DEMO_REQUESTS:
        agency_key = req_data["agency"]
        jurisdiction = req_data["jurisdiction"]
        records = req_data["records"]
        name = req_data["name"]
        agency_data = agencies[agency_key]
        
        try:
            letter_text, req_id, response_due = generate_letter(
                agency_key=agency_key,
                jurisdiction=jurisdiction,
                records_description=records,
                requester_name=name,
            )
            
            txt_path = output_dir / f"{req_id}.txt"
            txt_path.write_text(letter_text, encoding="utf-8")
            
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
            
            n8n_payload = {
                "request_id": req_id,
                "agency_name": agency_data["full_name"],
                "agency_email": agency_data["foia_email"],
                "jurisdiction": jurisdiction,
                "subject": records[:100],
                "requester_name": name,
                "user_email": "demo@example.com", # Default demo email
                "date_sent": date.today().isoformat(),
                "response_due": response_due,
                "letter_text": letter_text,
                "output_file": str(txt_path),
            }
            
            if trigger_n8n(n8n_payload):
                try:
                    mark_n8n_notified(req_id)
                except Exception:
                    pass
                    
            results.append({
                "id": req_id,
                "agency": agency_key,
                "status": "Success"
            })
        except Exception as e:
            results.append({
                "agency": agency_key,
                "status": "Failed",
                "error": str(e)
            })
            
    return {"results": results}
