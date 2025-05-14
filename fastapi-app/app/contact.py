from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# === FIND CONTACT PAGE ===
def find_contact_url(base_url):
    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            link_text = link.text.strip().lower()
            link_href = link['href'].lower()
            if (
                'contact' in link_text
                or 'get in touch' in link_text
                or 'contact-us' in link_href
            ):
                return (
                    link['href']
                    if 'http' in link['href']
                    else base_url.rstrip('/') + '/' + link['href'].lstrip('/')
                )
    except Exception:
        return None

# === FILL CONTACT FORM USING SELENIUM ===
def fill_contact_form(contact_url, form_data):
    try:
        driver = webdriver.Chrome()
        driver.get(contact_url)
        time.sleep(3)

        # Find all forms, skip those with class/id containing 'sidebar' or 'popup'
        forms = driver.find_elements(By.TAG_NAME, "form")
        main_forms = []
        for f in forms:
            form_id = (f.get_attribute('id') or '').lower()
            form_class = (f.get_attribute('class') or '').lower()
            if 'sidebar' in form_id or 'sidebar' in form_class or 'popup' in form_id or 'popup' in form_class:
                continue
            main_forms.append(f)
        if not main_forms:
            main_forms = forms  # fallback: use all forms if none left

        def find_and_fill(possible_names, value):
            if not value:
                return False
            for form in main_forms:
                # Try by name, id, placeholder (contains, not just equals)
                for name in possible_names:
                    # By name contains
                    try:
                        el = form.find_element(By.XPATH, f".//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                        if el.get_attribute('type') in [None, '', 'text', 'email', 'tel', 'number', 'password'] and not el.get_attribute('value'):
                            el.clear()
                            el.send_keys(value)
                            return True
                    except Exception:
                        pass
                    # By id contains
                    try:
                        el = form.find_element(By.XPATH, f".//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                        if el.get_attribute('type') in [None, '', 'text', 'email', 'tel', 'number', 'password'] and not el.get_attribute('value'):
                            el.clear()
                            el.send_keys(value)
                            return True
                    except Exception:
                        pass
                    # By placeholder contains
                    try:
                        el = form.find_element(By.XPATH, f".//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                        if el.get_attribute('type') in [None, '', 'text', 'email', 'tel', 'number', 'password'] and not el.get_attribute('value'):
                            el.clear()
                            el.send_keys(value)
                            return True
                    except Exception:
                        pass
                # Try for astralpipes: fill by partial match for 'mobile' and 'pincode' in any attribute
                try:
                    if value:
                        inputs = form.find_elements(By.XPATH, ".//input")
                        for el in inputs:
                            attrs = [el.get_attribute('name') or '', el.get_attribute('id') or '', el.get_attribute('placeholder') or '']
                            attrs = [a.lower() for a in attrs]
                            if any(n in a for n in possible_names for a in attrs):
                                if el.is_displayed() and not el.get_attribute('value'):
                                    el.clear()
                                    el.send_keys(value)
                                    return True
                except Exception:
                    pass
                # Try textarea
                for name in possible_names:
                    try:
                        el = form.find_element(By.XPATH, f".//textarea[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                        if not el.get_attribute('value'):
                            el.clear()
                            el.send_keys(value)
                            return True
                    except Exception:
                        pass
                    try:
                        el = form.find_element(By.XPATH, f".//textarea[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                        if not el.get_attribute('value'):
                            el.clear()
                            el.send_keys(value)
                            return True
                    except Exception:
                        pass
                    try:
                        el = form.find_element(By.XPATH, f".//textarea[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                        if not el.get_attribute('value'):
                            el.clear()
                            el.send_keys(value)
                            return True
                    except Exception:
                        pass
                # As a last resort, try to fill any empty visible text input in main form
                try:
                    if value:
                        inputs = form.find_elements(By.XPATH, ".//input[@type='text' or @type='email' or @type='tel' or @type='number' or @type='password']")
                        for el in inputs:
                            if el.is_displayed() and not el.get_attribute('value'):
                                el.clear()
                                el.send_keys(value)
                                return True
                except Exception:
                    pass
            return False

        # Try to fill name
        find_and_fill(["name", "your-name", "fullname", "full_name", "contactname", "contact_name"], form_data["name"])
        # Try to fill email
        find_and_fill(["email", "your-email", "mail", "contactemail", "contact_email"], form_data["email"])
        # Try to fill message/comment
        filled_message = find_and_fill(["message", "comment", "your-message", "enquiry", "query", "description", "body", "content"], form_data["message"])
        if not filled_message:
            try:
                for form in main_forms:
                    el = form.find_element(By.XPATH, ".//textarea")
                    if not el.get_attribute('value'):
                        el.clear()
                        el.send_keys(form_data["message"])
                        break
            except Exception:
                pass
        # Try to fill phone/mobile
        find_and_fill(["phone", "mobile", "contactphone", "contact_phone", "phonenumber", "phone_number", "txtmobile"], form_data.get("phone", ""))
        # Try to fill country
        find_and_fill(["country", "your-country", "contactcountry", "contact_country"], form_data.get("country", ""))
        # Try to fill city
        find_and_fill(["city", "your-city", "contactcity", "contact_city", "txtcity"], form_data.get("city", ""))
        # Try to fill state
        find_and_fill(["state", "your-state", "contactstate", "contact_state"], form_data.get("state", ""))
        # Try to fill pincode
        find_and_fill(["pincode", "pin", "zipcode", "zip", "postal", "postalcode", "postal_code", "txtpincode"], form_data.get("pincode", ""))

        # Try clicking the submit button in the main form
        try:
            for form in main_forms:
                try:
                    submit_button = form.find_element(By.XPATH, ".//input[@type='submit'] | .//button[@type='submit'] | .//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]")
                    submit_button.click()
                    time.sleep(5)
                    break
                except Exception:
                    continue
        except Exception:
            driver.quit()
            return False

        # After submission, check for success indicators
        page_source = driver.page_source.lower()
        success_indicators = [
            "thank you", "success", "submitted", "we have received", "your message has been sent", "we will contact you", "form has been received"
        ]
        is_success = False
        for indicator in success_indicators:
            if indicator in page_source:
                is_success = True
                break
        driver.quit()
        return is_success
    except Exception:
        return False