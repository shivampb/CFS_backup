from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.config import MAX_WORKERS
from app.core.navigator import find_contact_url
from app.core.form_filler import fill_contact_form

def process_website(site, form_data):
    try:
        if not (site.startswith("http://") or site.startswith("https://")):
            site = "https://" + site

        print(f"🔄 Processing: {site}", flush=True)


        contact_url = find_contact_url(site)
        if not contact_url:
            print(f"⚠️  {site}: No contact page found", flush=True)
            return (site, False, "No contact page found")

        print(f"📝 {site}: Found contact URL: {contact_url}. Start filling...", flush=True)

        result = fill_contact_form(contact_url, form_data)
        if result:
            print(f"✅ {site}: Form submitted successfully", flush=True)
            return (site, True, "Success")
        
        print(f"❌ {site}: Form submission failed", flush=True)
        return (site, False, "Form submission failed")
    except Exception as e:
        print(f"💀 {site}: Error: {e}", flush=True)
        return (site, False, str(e))


def process_websites(websites_list, form_data):
    success_list = []
    contact_not_found = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_site = {
            executor.submit(process_website, site, form_data): site
            for site in websites_list
        }

        for future in as_completed(future_to_site):
            site, success, message = future.result()
            if success:
                success_list.append(site)
                print(f"✔️ {site}: Form submitted successfully")
            else:
                contact_not_found.append(site)
                print(f"❌ {site}: {message}")

    return success_list, contact_not_found
