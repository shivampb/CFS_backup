import logging
import sys
from pathlib import Path
from fastapi import FastAPI, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.core.engine import process_websites

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS - Updated configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Existing routes
@app.api_route("/", methods=["GET", "POST"], response_class=HTMLResponse)
async def main_form(request: Request):
    if request.method == "GET":
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "success_list": [],
                "contact_not_found": [],
                "contact_not_found_count": 0,
                "success_rate": None,
                # Clear all form fields on refresh
                "websites": "",
                "name": "",
                "email": "",
                "message": "",
                "phone": "",
                "country": "",
                "city": "",
                "state": "",
                "pincode": "",
                "subject": "",
            },
        )
    form = await request.form()
    websites = str(form.get("websites", ""))
    name = str(form.get("name", ""))
    email = str(form.get("email", ""))
    message = str(form.get("message", ""))
    phone = str(form.get("phone", ""))
    country = str(form.get("country", ""))
    city = str(form.get("city", ""))
    state = str(form.get("state", ""))
    pincode = str(form.get("pincode", ""))
    subject = str(form.get("subject", ""))
    websites_list = [w.strip() for w in websites.splitlines() if w.strip()]
    if not websites_list:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "success_list": [],
                "contact_not_found": [],
                "contact_not_found_count": 0,
                "success_rate": None,
                "error": "Please enter at least one website URL.",
                "websites": websites,
                "name": name,
                "email": email,
                "message": message,
                "phone": phone,
                "country": country,
                "city": city,
                "state": state,
                "pincode": pincode,
                "subject": subject,
            },
        )
    form_data = {
        "name": name.strip(),
        "email": email.strip(),
        "message": message.strip(),
        "phone": phone.strip(),
        "country": country.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "pincode": pincode.strip(),
        "subject": subject.strip(),
    }
    # Process websites in parallel without blocking event loop
    success_list, contact_not_found = await run_in_threadpool(process_websites, websites_list, form_data)
    total_sites = len(websites_list)
    success_rate = (len(success_list) / total_sites) * 100 if total_sites else 0
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "success_list": success_list,
            "contact_not_found": contact_not_found,
            "contact_not_found_count": len(contact_not_found),
            "success_rate": f"{success_rate:.2f}",
            # Clear all form fields after POST/refresh
            "websites": "",
            "name": "",
            "email": "",
            "message": "",
            "phone": "",
            "country": "",
            "city": "",
            "state": "",
            "pincode": "",
            "subject": "",
        },
    )
