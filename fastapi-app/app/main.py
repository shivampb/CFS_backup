from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.contact import find_contact_url, fill_contact_form, process_websites

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.api_route("/", methods=["GET", "POST"], response_class=HTMLResponse)
async def main_form(request: Request):
    if request.method == "GET":
        return templates.TemplateResponse("index.html", {
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
            "pincode": ""
        })
    form = await request.form()
    websites = form.get("websites", "")
    name = form.get("name", "")
    email = form.get("email", "")
    message = form.get("message", "")
    phone = form.get("phone", "")
    country = form.get("country", "")
    city = form.get("city", "")
    state = form.get("state", "")
    pincode = form.get("pincode", "")
    subject = form.get("subject", "")
    websites_list = [w.strip() for w in websites.splitlines() if w.strip()]
    if not websites_list:
        return templates.TemplateResponse("index.html", {
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
            "pincode": pincode
        })
    form_data = {
        "name": name.strip(),
        "email": email.strip(),
        "message": message.strip(),
        "phone": phone.strip(),
        "country": country.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "pincode": pincode.strip(),
        "subject": subject.strip()
    }
    # Process websites in parallel
    success_list, contact_not_found = process_websites(websites_list, form_data)
    total_sites = len(websites_list)
    success_rate = (len(success_list) / total_sites) * 100 if total_sites else 0
    return templates.TemplateResponse("index.html", {
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
        "pincode": ""
    })