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
                # Double check: if it has "contact" explicitly, maybe ignore popup indicator
                if "contact" in form_id or "contact" in form_class:
                     continue
                return True

        # Check form position/style
        style = (form.get_attribute("style") or "")
        if "position: fixed" in style or "position: absolute" in style or "z-index" in style:
            return True

        # Check form size (small forms are likely not contact forms)
        inputs = form.find_elements(By.TAG_NAME, "input")
        textareas = form.find_elements(By.TAG_NAME, "textarea")
        if len(inputs) + len(textareas) < 2:  # Too few fields for a contact form
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
            "write-to-us", "send-message", "appointment", "booking", "consultation"
        ]

        # Check for contact form indicators
        for indicator in contact_indicators:
            if indicator in form_id or indicator in form_class or indicator in form_html:
                return True

        # Check for typical contact form fields
        required_fields = ["name", "email", "message", "phone", "subject"]
        field_count = 0

        # Check input fields
        inputs = form.find_elements(By.TAG_NAME, "input")
        textareas = form.find_elements(By.TAG_NAME, "textarea")

        for el in inputs + textareas:
            el_name = (el.get_attribute("name") or "").lower()
            el_id = (el.get_attribute("id") or "").lower()
            el_placeholder = (el.get_attribute("placeholder") or "").lower()
            el_type = (el.get_attribute("type") or "").lower()

            if el_type == "hidden" or el_type == "submit":
                continue

            for field in required_fields:
                if field in el_name or field in el_id or field in el_placeholder:
                    field_count += 1
                    break

        # If we found most of the typical contact form fields
        if field_count >= 1: # Lowered threshold to 1 if we are desperate or it's a simple form
            return True
            
        # Fallback: if it has at least 3 visible inputs + textareas, consider it
        visible_inputs = [i for i in inputs if i.is_displayed()]
        visible_textareas = [t for t in textareas if t.is_displayed()]
        if len(visible_inputs) + len(visible_textareas) >= 3:
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
                        for idx, option in enumerate(select.options):
                            if value_to_select.lower() in option.text.lower():
                                select.select_by_index(idx)
                                time.sleep(FILL_DELAY)
                                found = True
                                break
                        if found:
                            continue

                # If no specific match or selection failed, just pick the first meaningful option
                if len(select.options) > 1:
                    try:
                        # Randomly select reasonably if many options, else first meaningful
                        valid_options = []
                        for i, opt in enumerate(select.options):
                            if "select" not in opt.text.lower() and "choose" not in opt.text.lower() and opt.text.strip():
                                valid_options.append(i)
                        
                        if valid_options:
                            idx = random.choice(valid_options)
                            select.select_by_index(idx)
                        else:
                            select.select_by_index(1) # Fallback
                        
                        time.sleep(FILL_DELAY)
                    except:
                        pass
                        
            except Exception:
                pass
    except Exception:
        pass


def fill_random_data(form, form_data=None):
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
                placeholder = (el.get_attribute("placeholder") or "").lower()
                
                # Skip special types
                if etype in ["hidden", "submit", "button", "image", "file", "reset", "search"]:
                    continue

                # Skip checkboxes and radios here (handled separately, but if empty text nearby?)
                if etype in ["checkbox", "radio"]:
                    continue
                
                # Skip if it looks like a search field
                if "search" in name or "search" in eid or "search" in placeholder:
                    continue
                    
                # Generate value based on type or name context
                val = ""
                if "email" in etype or "email" in name or "mail" in name:
                    val = f"user{random.randint(1000,9999)}@example.com"
                elif "tel" in etype or "number" in etype or "phone" in name or "zip" in name or "code" in name or "mobile" in name:
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
                print(f"    🎲 Filled random data '{val}' into field '{name or eid}'", flush=True)
            except:
                pass
                
        # Textareas
        fallback_msg = (form_data.get("message") if form_data and isinstance(form_data, dict) and form_data.get("message") else None) or "Looking forward to hearing from you. Thanks."
        textareas = form.find_elements(By.TAG_NAME, "textarea")
        for el in textareas:
            try:
                if el.is_displayed() and el.is_enabled() and not el.get_attribute("value"):
                    el.clear()
                    el.send_keys(fallback_msg)
                    time.sleep(0.1)
                    print(f"    ✏️  Filled 'message' in textarea field (fallback)", flush=True)
            except:
                pass
    except:
        pass


def click_relevant_checkboxes(form):
    """Click relevant checkboxes in the form, including Captchas"""
    try:
        # Important keywords that indicate required checkboxes
        important_keywords = [
            "agree", "accept", "consent", "confirm", "privacy", "policy",
            "terms", "conditions", "required", "human", "robot",
            "recaptcha", "verify", "newsletter", "not a robot"
        ]

        # Find all checkboxes
        checkboxes = form.find_elements(By.XPATH, ".//input[@type='checkbox']")
        
        for checkbox in checkboxes:
            try:
                # Get all relevant attributes
                checkbox_id = (checkbox.get_attribute("id") or "").lower()
                checkbox_name = (checkbox.get_attribute("name") or "").lower()
                checkbox_class = (checkbox.get_attribute("class") or "").lower()
                checkbox_text = ""
                aria_label = (checkbox.get_attribute("aria-label") or "").lower()

                # Try to get associated label text
                try:
                    if checkbox_id:
                        label = form.find_element(By.XPATH, f".//label[@for='{checkbox_id}']")
                        checkbox_text = label.text.lower()
                except:
                    pass
                try:
                    label = checkbox.find_element(By.XPATH, "./ancestor::label")
                    checkbox_text += label.text.lower()
                except:
                    pass

                combined_text = f"{checkbox_id} {checkbox_name} {checkbox_class} {checkbox_text} {aria_label}"

                # Check if this checkbox seems important
                is_important = any(keyword in combined_text for keyword in important_keywords)

                if is_important and not checkbox.is_selected():
                    if checkbox.is_displayed() and checkbox.is_enabled():
                        checkbox.click()
                        time.sleep(FILL_DELAY)
                        print(f"    ☑️  Clicked checkbox: {combined_text[:50]}...", flush=True)

            except Exception:
                continue
        
        # Helper to click captcha elements
        def click_captcha_element(el, desc):
             try:
                 if el.is_displayed() and el.is_enabled():
                     # Check if it has a click listener or is a checkbox replacement
                     cname = (el.get_attribute("class") or "").lower()
                     eid = (el.get_attribute("id") or "").lower()
                     
                     # Only click if it's reasonably a checkbox/captcha
                     # Avoid clicking container divs unless they are specific
                     if "checkbox" in cname or "box" in cname or "anchor" in cname or "recaptcha" in cname or "recaptcha" in eid:
                         el.click()
                         print(f"    ☑️  Clicked potential captcha element ({desc}): {cname}", flush=True)
                         time.sleep(2) # Wait a bit as requested per "wait little"
             except:
                 pass

        # KEY ADDITION: Handle Non-standard Captchas (Ticket Icon)
        # 1. Look for elements with class/id containing recaptcha/captcha
        try:
            potential_captchas = form.find_elements(By.XPATH, 
                ".//*[contains(@class, 'recaptcha') or contains(@id, 'recaptcha') or contains(@class, 'captcha') or contains(@id, 'captcha')]")
            
            for el in potential_captchas:
                if el.tag_name in ["iframe", "script", "style", "link"]:
                    continue 
                click_captcha_element(el, "class/id match")
        except:
            pass
            
        # 2. Look for specific tick icons (SVG or i tags) often used in custom checkboxes
        try:
             icons = form.find_elements(By.XPATH, ".//i[contains(@class, 'fa-check') or contains(@class, 'icon-check')] | .//svg[contains(@class, 'check')]")
             for icon in icons:
                 # Check if parent is a checkbox container
                 parent = icon.find_element(By.XPATH, "./..")
                 parent_class = (parent.get_attribute("class") or "").lower()
                 if "check" in parent_class or "box" in parent_class:
                     click_captcha_element(parent, "icon parent")
        except:
            pass

    except Exception:
        pass
