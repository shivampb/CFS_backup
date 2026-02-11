import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.core.config import PAGE_LOAD_DELAY, SUBMIT_DELAY, FILL_DELAY
from app.core.browser import create_driver
from app.core.heuristics import (
    is_popup_or_newsletter_form,
    is_likely_contact_form,
    close_obstructions,
    fill_dropdowns,
    fill_random_data,
    click_relevant_checkboxes
)

def fill_contact_form(contact_url, form_data):
    """Attempt to find and fill a contact form on the given URL"""
    driver = None
    try:
        driver = create_driver()
        try:
            driver.get(contact_url)
            # Use WebDriverWait instead of sleep
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
        except Exception:
            # If timeout or no form found, continue with normal flow
            pass

        # Find all forms and filter intelligently
        forms = driver.find_elements(By.TAG_NAME, "form")
        main_forms = []

        # Try to close any blocking popups or cookie banners first
        close_obstructions(driver)

        # First, try to find forms that are explicitly contact forms
        for form in forms:
            if is_likely_contact_form(form) and not is_popup_or_newsletter_form(form):
                main_forms.append(form)

        # If no explicit contact form found, try forms with multiple fields that aren't popups
        if not main_forms:
            for form in forms:
                if not is_popup_or_newsletter_form(form):
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    textareas = form.find_elements(By.TAG_NAME, "textarea")
                    if len(inputs) + len(textareas) >= 3:  # Form has enough fields
                        main_forms.append(form)

        # If still no forms found, looking for a contact link and clicking it might help (SPA/JS nav)
        if not main_forms:
            try:
                # Common contact link text
                contact_keywords = ["contact", "get in touch", "support", "help", "enquiry"]
                links = driver.find_elements(By.TAG_NAME, "a")
                clicked = False
                for link in links:
                    if not link.is_displayed():
                        continue
                    text = link.text.lower()
                    href = (link.get_attribute("href") or "").lower()
                    
                    if any(k in text for k in contact_keywords) or any(k in href for k in contact_keywords):
                        # Avoid clicking mailto or tel links
                        if "mailto:" in href or "tel:" in href:
                            continue
                            
                        # Try to click
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", link)
                            time.sleep(0.5)
                            link.click()
                            clicked = True
                            time.sleep(PAGE_LOAD_DELAY + 1) # Wait for page load/modal
                            break
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", link)
                                clicked = True
                                time.sleep(PAGE_LOAD_DELAY + 1)
                                break
                            except:
                                pass
                
                if clicked:
                    # Re-scan for forms after navigation
                    forms = driver.find_elements(By.TAG_NAME, "form")
                    close_obstructions(driver)
                    # Re-run filtering logic (simplified for fallback)
                    main_forms = [f for f in forms if not is_popup_or_newsletter_form(f)]
                    if not main_forms:
                        main_forms = forms
            except:
                pass

        if not main_forms:
            # If still no forms found after all attempts, abort immediately
            if driver:
                driver.quit()
            return False

        print(f"    📄 {contact_url}: Found {len(main_forms)} potential form(s). Filling...", flush=True)


        # Last resort: use all forms if none left
        # (This is technically redundant due to the fast fail above unless we remove the fast fail block, 
        # but let's keep logic cleaner - if main_forms is still empty here, we failed).
        # However, the code above assigns main_forms = forms in SPA block if empty. 
        # So we proceed if main_forms has items.
        
        def find_and_fill(possible_names, value):
            if not value:
                return False
            for form in main_forms:
                # Try by name, id, placeholder (contains, not just equals), but ignore search fields
                for name in possible_names:
                    # By name contains
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}') and not(contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search'))]",
                        )
                        if el.get_attribute("type") in [None, "", "text", "email", "tel", "number", "password"] and not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            print(f"    ✏️  Filled '{name}' field by name match", flush=True)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                    # By id contains
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}') and not(contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search'))]",
                        )
                        if el.get_attribute("type") in [None, "", "text", "email", "tel", "number", "password"] and not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            print(f"    ✏️  Filled '{name}' field by ID match", flush=True)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                    # By placeholder contains
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}') and not(contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search'))]",
                        )
                        if el.get_attribute("type") in [None, "", "text", "email", "tel", "number", "password"] and not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            print(f"    ✏️  Filled '{name}' field by placeholder match", flush=True)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                
                # Try to match placeholder exactly to user field name
                try:
                    inputs = form.find_elements(By.XPATH, ".//input")
                    for el in inputs:
                        placeholder = (el.get_attribute("placeholder") or "").strip().lower()
                        if placeholder and not "search" in placeholder:
                            for user_field in form_data:
                                if (user_field in placeholder or (user_field == "email" and "email" in placeholder)) and form_data[user_field]:
                                    if el.is_displayed() and not el.get_attribute("value"):
                                        el.clear()
                                        el.send_keys(form_data[user_field])
                                        print(f"    ✏️  Filled '{user_field}' in field with placeholder '{placeholder}'", flush=True)
                                        time.sleep(FILL_DELAY)
                                        return True
                except Exception:
                    pass

                # Try to match by associated LABEL text
                try:
                    inputs = form.find_elements(By.XPATH, ".//input")
                    for el in inputs:
                        if not el.is_displayed() or el.get_attribute("type") in ["hidden", "submit", "button", "image", "file", "checkbox", "radio", "reset"]:
                            continue
                            
                        # Get label text
                        label_text = ""
                        eid = el.get_attribute("id")
                        # 1. By 'for' attribute
                        if eid:
                            try:
                                label_el = form.find_element(By.XPATH, f".//label[@for='{eid}']")
                                label_text += label_el.text
                            except:
                                pass
                        # 2. By parent label
                        try:
                            parent_label = el.find_element(By.XPATH, "./ancestor::label")
                            label_text += parent_label.text
                        except:
                            pass
                        # 3. By preceding sibling label (common in some CMS)
                        try:
                             # Look for a label preceding this input (possibly separated by BRs or spans)
                             preceding_label = el.find_element(By.XPATH, "./preceding::label[1]")
                             # Check if it's close enough (naive check: same parent or close ancestor)
                             # Or just check if the text matches the field we want
                             label_text += preceding_label.text
                        except:
                            pass

                        label_text = label_text.lower()
                        
                        for name in possible_names:
                            if name in label_text:
                                if not el.get_attribute("value"):
                                    el.clear()
                                    el.send_keys(value)
                                    print(f"    ✏️  Filled '{name}' field by label match: '{label_text}'", flush=True)
                                    time.sleep(FILL_DELAY)
                                    return True
                except Exception:
                    pass

                # Try textarea
                for name in possible_names:
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//textarea[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]",
                        )
                        if not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            print(f"    ✏️  Filled textarea '{name}'", flush=True)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
            return False

        # Use all collected user info for relevant fields
        find_and_fill(["name", "your-name", "fullname", "full_name", "contactname", "contact_name"], form_data["name"])
        find_and_fill(["email", "your-email", "mail", "contactemail", "contact_email", "contact[email]"], form_data["email"])
        filled_message = find_and_fill(["message", "comment", "your-message", "enquiry", "query", "description", "body", "content"], form_data["message"])
        
        if not filled_message:
            try:
                for form in main_forms:
                    el = form.find_element(By.XPATH, ".//textarea")
                    if not el.get_attribute("value"):
                        el.clear()
                        el.send_keys(form_data["message"])
                        time.sleep(FILL_DELAY)
                        break
            except Exception:
                pass
                
        find_and_fill(["phone", "mobile", "contactphone", "contact_phone", "phonenumber", "phone_number", "txtmobile"], form_data.get("phone", ""))
        find_and_fill(["country", "your-country", "contactcountry", "contact_country"], form_data.get("country", ""))
        find_and_fill(["city", "your-city", "contactcity", "contact_city", "txtcity"], form_data.get("city", ""))
        find_and_fill(["state", "your-state", "contactstate", "contact_state"], form_data.get("state", ""))
        find_and_fill(["pincode", "pin", "zipcode", "zip", "postal", "postalcode", "postal_code", "txtpincode"], form_data.get("pincode", ""))
        find_and_fill(["subject", "your-subject", "contactsubject", "contact_subject", "enquiry_subject", "txtsubject"], form_data.get("subject", ""))

        # Handle dropdown fields
        try:
            for form in main_forms:
                fill_dropdowns(form, form_data)
        except Exception:
            pass

        # Fill remaining empty fields with random data to ensure submission
        try:
            for form in main_forms:
                fill_random_data(form)
        except Exception:
            pass

        # Checkboxes
        try:
            for form in main_forms:
                click_relevant_checkboxes(form)

                # Handle reCAPTCHA frames
                recaptcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
                for frame in recaptcha_frames:
                    try:
                        driver.switch_to.frame(frame)
                        checkbox = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border")
                        if checkbox.is_displayed() and checkbox.is_enabled():
                            checkbox.click()
                            time.sleep(SUBMIT_DELAY)
                        driver.switch_to.default_content()
                    except Exception:
                        driver.switch_to.default_content()
                        continue
        except Exception:
            pass

        # Submit
        try:
            for form in main_forms:
                try:
                    submit_button = form.find_element(
                        By.XPATH,
                        ".//input[@type='submit'] | "
                        ".//button[@type='submit'] | "
                        ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')] | "
                        ".//button[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'subscribe')] | "
                        ".//button[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'newsletter-form__button')] | "
                        ".//button[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'commit')] | "
                        ".//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                    )
                    submit_button.click()
                    print(f"    🚀 {contact_url}: Clicked submit...", flush=True)
                    time.sleep(SUBMIT_DELAY)  # Wait for submission to complete
                    break
                except Exception:
                    continue
        except Exception:
            if driver is not None:
                driver.quit()
            return False

        # After submission, check for success indicators
        time.sleep(4) # Wait a bit for response (increased for AJAX)
        page_source = driver.page_source.lower()
        current_url = driver.current_url.lower()
        success_indicators = [
            "thank you", "success", "submitted", "we have received",
            "your message has been sent", "we will contact you",
            "form has been received", "message sent", "inquiry sent",
            "thank-you", "submission", "sent successfully",
            "response-output", "wpcf7-response-output", "message was sent"
        ]
        
        is_success = False
        # Check URL for success indicators
        if "thank" in current_url or "success" in current_url or "sent" in current_url:
            is_success = True
            print(f"    ✅ {contact_url}: Success confirmed by URL match", flush=True)
            
        if not is_success:
            for indicator in success_indicators:
                if indicator in page_source:
                    is_success = True
                    print(f"    ✅ {contact_url}: Success confirmed by keyword '{indicator}'", flush=True)
                    break
                    
        if not is_success:
             print(f"    ❌ {contact_url}: No success indicators found", flush=True)
                    
        driver.quit()
        return is_success
    except Exception as e:
        if "driver" in locals() and driver is not None:
            driver.quit()
        return False
