from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import random
import string
from app.core.config import FILL_DELAY, SUBMIT_DELAY

def is_popup_or_newsletter_form(form):
    """Check if a form is likely a popup or newsletter form"""
    try:
        # Get all form attributes
        form_id = (form.get_attribute("id") or "").lower()
        form_class = (form.get_attribute("class") or "").lower()
        form_html = form.get_attribute("outerHTML").lower()
        
        # KEY CHANGE: If it has a textarea, assume it Is a contact form (or extended form) 
        # and NOT a simple newsletter popup, regardless of container naming.
        if form.find_elements(By.TAG_NAME, "textarea"):
            return False

        # Keywords that indicate popup/newsletter forms
        popup_indicators = [
            "popup", "modal", "newsletter", "subscribe", "sidebar", "overlay",
            "floating", "notification", "alert", "chat", "messenger",
            "livechat", "drift", "intercom", "zendesk", "cookie", "gdpr",
            "promotion", "offer", "discount", "sale", "signup", "login",
            "register"
        ]

        # Check form attributes for popup indicators
        for indicator in popup_indicators:
            if indicator in form_id or indicator in form_class or indicator in form_html:
                return True

        # Check form position/style
        style = (form.get_attribute("style") or "")
        if "position: fixed" in style or "position: absolute" in style or "z-index" in style:
            return True

        # Check form size (small forms are likely not contact forms)
        inputs = form.find_elements(By.TAG_NAME, "input")
        textareas = form.find_elements(By.TAG_NAME, "textarea")
        if len(inputs) + len(textareas) < 3:  # Too few fields for a contact form
            return True

        return False
    except Exception:
        return False


def is_likely_contact_form(form):
    """Check if a form is likely the main contact form"""
    try:
        form_id = (form.get_attribute("id") or "").lower()
        form_class = (form.get_attribute("class") or "").lower()
        form_html = form.get_attribute("outerHTML").lower()

        # Keywords that indicate contact forms
        contact_indicators = [
            "contact", "enquiry", "inquiry", "feedback", "support",
            "help-form", "contact-us", "get-in-touch", "reach-us",
            "write-to-us", "send-message"
        ]

        # Check for contact form indicators
        for indicator in contact_indicators:
            if indicator in form_id or indicator in form_class or indicator in form_html:
                return True

        # Check for typical contact form fields
        required_fields = ["name", "email", "message"]
        field_count = 0

        # Check input fields
        inputs = form.find_elements(By.TAG_NAME, "input")
        textareas = form.find_elements(By.TAG_NAME, "textarea")

        for el in inputs + textareas:
            el_name = (el.get_attribute("name") or "").lower()
            el_id = (el.get_attribute("id") or "").lower()
            el_placeholder = (el.get_attribute("placeholder") or "").lower()

            for field in required_fields:
                if field in el_name or field in el_id or field in el_placeholder:
                    field_count += 1
                    break

        # If we found most of the typical contact form fields
        if field_count >= 2:
            return True

        return False
    except Exception:
        return False


def close_obstructions(driver):
    """Try to close popups, cookie banners, and other obstructions"""
    try:
        # Common selectors for close buttons and cookie acceptance
        selectors = [
            "button[aria-label='Close']",
            "button[aria-label='close']",
            ".close",
            ".close-button",
            ".modal-close",
            ".popup-close",
            "#close-popup",
            # Cookie banners
            "button[id*='cookie']",
            "button[class*='cookie']",
            "a[class*='cookie']",
            "button[id*='accept']",
            "button[class*='accept']",
            "button[class*='agree']",
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed() and el.is_enabled():
                        # Check text for cookie/accept keywords to avoid clicking random buttons
                        text = el.text.lower()
                        if any(x in text for x in ['accept', 'agree', 'got it', 'allow', 'close', 'x']):
                            try:
                                el.click()
                                time.sleep(0.5)
                            except:
                                driver.execute_script("arguments[0].click();", el)
            except:
                pass
    except:
        pass


def fill_dropdowns(form, form_data):
    """Handle <select> dropdown fields"""
    try:
        selects = form.find_elements(By.TAG_NAME, "select")
        for select_el in selects:
            try:
                if not select_el.is_displayed():
                    continue
                    
                select = Select(select_el)
                name = (select_el.get_attribute("name") or "").lower()
                select_id = (select_el.get_attribute("id") or "").lower()
                
                # Dictionary mapping user fields to dropdown types
                mappings = {
                    "country": ["country", "nation"],
                    "state": ["state", "province", "region"],
                    "subject": ["subject", "topic", "inquiry", "reason"],
                    "budget": ["budget", "price"],
                }
                
                # Try to find a match in our form data
                value_to_select = None
                
                # Check if this dropdown matches any of our known fields
                for field, keywords in mappings.items():
                    if any(k in name or k in select_id for k in keywords):
                        if field in form_data and form_data[field]:
                            value_to_select = form_data[field]
                            break
                
                if value_to_select:
                    # Try to select by visible text
                    try:
                        select.select_by_visible_text(value_to_select)
                        time.sleep(FILL_DELAY)
                        continue
                    except:
                        # Try case-insensitive partial match
                        found = False
                        for option in select.options:
                            if value_to_select.lower() in option.text.lower():
                                select.select_by_index(option.index)
                                time.sleep(FILL_DELAY)
                                found = True
                                break
                        if found:
                            continue

                # If no specific match or selection failed, and it's a required valid field
                # just pick the first meaningful option 
                if len(select.options) > 1:
                    try:
                        # Check if first option is a placeholder
                        first_text = select.options[0].text.lower()
                        if "select" in first_text or "choose" in first_text or first_text == "":
                            select.select_by_index(1)
                        else:
                            select.select_by_index(0)
                        time.sleep(FILL_DELAY)
                    except:
                        pass
                        
            except Exception:
                pass
    except Exception:
        pass


def fill_random_data(form):
    """Fill empty input fields with random data to ensure submission"""
    try:
        # Inputs
        inputs = form.find_elements(By.TAG_NAME, "input")
        for el in inputs:
            try:
                if not el.is_displayed() or not el.is_enabled():
                    continue
                
                # Skip if already has value
                if el.get_attribute("value"):
                    continue
                    
                etype = (el.get_attribute("type") or "text").lower()
                name = (el.get_attribute("name") or "").lower()
                eid = (el.get_attribute("id") or "").lower()
                
                # Skip special types
                if etype in ["hidden", "submit", "button", "image", "file", "checkbox", "radio", "reset", "search"]:
                    continue
                
                # Skip if it looks like a search field
                if "search" in name or "search" in eid:
                    continue
                    
                # Generate value based on type or name context
                val = ""
                if "email" in etype or "email" in name:
                    val = f"user{random.randint(1000,9999)}@example.com"
                elif "tel" in etype or "number" in etype or "phone" in name or "zip" in name or "code" in name:
                    val = "".join(random.choices(string.digits, k=10))
                elif "url" in etype or "website" in name:
                    val = "https://example.com"
                elif "date" in etype:
                    val = "2025-01-01" 
                elif "time" in etype:
                    val = "10:00"
                else:
                    # Generic text
                    val = "".join(random.choices(string.ascii_letters, k=8))
                
                el.clear()
                el.send_keys(val)
                time.sleep(0.1)
            except:
                pass
                
        # Textareas
        textareas = form.find_elements(By.TAG_NAME, "textarea")
        for el in textareas:
            try:
                if el.is_displayed() and el.is_enabled() and not el.get_attribute("value"):
                    el.send_keys("Looking forward to hearing from you. Thanks.")
                    time.sleep(0.1)
            except:
                pass
    except:
        pass


def click_relevant_checkboxes(form):
    """Click relevant checkboxes in the form"""
    try:
        # Important keywords that indicate required checkboxes
        important_keywords = [
            "agree", "accept", "consent", "confirm", "privacy", "policy",
            "terms", "conditions", "required", "human", "robot",
            "recaptcha", "verify", "newsletter"
        ]

        # Find all checkboxes in the form
        checkboxes = form.find_elements(By.XPATH, ".//input[@type='checkbox']")

        for checkbox in checkboxes:
            try:
                # Get all relevant attributes
                checkbox_id = (checkbox.get_attribute("id") or "").lower()
                checkbox_name = (checkbox.get_attribute("name") or "").lower()
                checkbox_class = (checkbox.get_attribute("class") or "").lower()
                checkbox_text = ""

                # Try to get associated label text
                try:
                    # First try finding label by for attribute
                    if checkbox_id:
                        label = form.find_element(
                            By.XPATH, f".//label[@for='{checkbox_id}']"
                        )
                        checkbox_text = label.text.lower()
                except:
                    try:
                        # Then try finding parent label
                        label = checkbox.find_element(By.XPATH, "./ancestor::label")
                        checkbox_text = label.text.lower()
                    except:
                        pass

                # Check if this checkbox seems important
                is_important = any(
                    keyword in checkbox_id
                    or keyword in checkbox_name
                    or keyword in checkbox_class
                    or keyword in checkbox_text
                    for keyword in important_keywords
                )

                # Click if it's important and not already checked
                if is_important and not checkbox.is_selected():
                    if checkbox.is_displayed() and checkbox.is_enabled():
                        checkbox.click()
                        time.sleep(FILL_DELAY)

            except Exception:
                continue

    except Exception:
        pass
