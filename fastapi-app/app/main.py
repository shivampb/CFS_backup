from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.contact import find_contact_url, fill_contact_form

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
    success_list = []
    contact_not_found = []
    for site in websites_list:
        # Automatically add https:// if missing
        if not (site.startswith("http://") or site.startswith("https://")):
            site = "https://" + site
        contact_url = find_contact_url(site)
        if not contact_url:
            contact_not_found.append(site)
            continue
        try:
            result = fill_contact_form(contact_url, form_data)
        except Exception:
            # If any error occurs (e.g., no form, driver error), treat as not found
            result = False
        if result:
            success_list.append(site)
        else:
            contact_not_found.append(site)
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