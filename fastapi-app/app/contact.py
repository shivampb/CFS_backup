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

        def find_and_fill(possible_names, value):
            if not value:
                return False
            # Try by name, id, placeholder (contains, not just equals)
            for name in possible_names:
                # By name contains
                try:
                    el = driver.find_element(By.XPATH, f"//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                    if el.get_attribute('type') in [None, '', 'text', 'email', 'tel', 'number'] and not el.get_attribute('value'):
                        el.clear()
                        el.send_keys(value)
                        return True
                except Exception:
                    pass
                # By id contains
                try:
                    el = driver.find_element(By.XPATH, f"//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                    if el.get_attribute('type') in [None, '', 'text', 'email', 'tel', 'number'] and not el.get_attribute('value'):
                        el.clear()
                        el.send_keys(value)
                        return True
                except Exception:
                    pass
                # By placeholder contains
                try:
                    el = driver.find_element(By.XPATH, f"//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                    if el.get_attribute('type') in [None, '', 'text', 'email', 'tel', 'number'] and not el.get_attribute('value'):
                        el.clear()
                        el.send_keys(value)
                        return True
                except Exception:
                    pass
            # Try textarea
            for name in possible_names:
                try:
                    el = driver.find_element(By.XPATH, f"//textarea[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                    if not el.get_attribute('value'):
                        el.clear()
                        el.send_keys(value)
                        return True
                except Exception:
                    pass
                try:
                    el = driver.find_element(By.XPATH, f"//textarea[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                    if not el.get_attribute('value'):
                        el.clear()
                        el.send_keys(value)
                        return True
                except Exception:
                    pass
                try:
                    el = driver.find_element(By.XPATH, f"//textarea[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]" )
                    if not el.get_attribute('value'):
                        el.clear()
                        el.send_keys(value)
                        return True
                except Exception:
                    pass
            # As a last resort, try to fill any empty visible text input
            try:
                if value:
                    inputs = driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @type='tel' or @type='number']")
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
                el = driver.find_element(By.XPATH, "//textarea")
                if not el.get_attribute('value'):
                    el.clear()
                    el.send_keys(form_data["message"])
            except Exception:
                pass
        # Try to fill phone
        find_and_fill(["phone", "mobile", "contactphone", "contact_phone", "phonenumber", "phone_number"], form_data.get("phone", ""))
        # Try to fill country
        find_and_fill(["country", "your-country", "contactcountry", "contact_country"], form_data.get("country", ""))
        # Try to fill city
        find_and_fill(["city", "your-city", "contactcity", "contact_city"], form_data.get("city", ""))
        # Try to fill state
        find_and_fill(["state", "your-state", "contactstate", "contact_state"], form_data.get("state", ""))
        # Try to fill pincode
        find_and_fill(["pincode", "pin", "zipcode", "zip", "postal", "postalcode", "postal_code"], form_data.get("pincode", ""))

        # Try clicking the submit button (input or button with type submit or text 'send')
        try:
            submit_button = driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit'] | //button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]" )
            submit_button.click()
            time.sleep(5)
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