from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# === CONFIGURATION ===
FILL_DELAY = 0.1  # reduced delay after filling each field
PAGE_LOAD_DELAY = 0.5  # reduced delay after loading a contact page
SUBMIT_DELAY = 0.5  # reduced delay after clicking submit
SWAP_DELAY = 0.1  # reduced delay between sites
MAX_TIMEOUT = 10  # maximum timeout for page load
MAX_WORKERS = 5  # number of parallel workers


def process_website(site, form_data):
    try:
        if not (site.startswith("http://") or site.startswith("https://")):
            site = "https://" + site

        contact_url = find_contact_url(site)
        if not contact_url:
            return (site, False, "No contact page found")

        result = fill_contact_form(contact_url, form_data)
        if result:
            return (site, True, "Success")
        return (site, False, "Form submission failed")
    except Exception as e:
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


def find_contact_url(base_url):
    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            link_text = link.text.strip().lower()
            link_href = link["href"].lower()
            if (
                "contact" in link_text
                or "get in touch" in link_text
                or "contact-us" in link_href
            ):
                return (
                    link["href"]
                    if "http" in link["href"]
                    else base_url.rstrip("/") + "/" + link["href"].lstrip("/")
                )
    except Exception:
        return None


# === FILL CONTACT FORM USING SELENIUM ===
def fill_contact_form(contact_url, form_data):
    driver = None
    try:
        # Configure Chrome to run in headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # WebGL and DevTools configurations
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-webgl2")
        # Performance optimizations
        chrome_options.add_argument("--disable-javascript-harmony-shipping")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--dns-prefetch-disable")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.page_load_strategy = (
            "eager"  # Don't wait for all resources to load
        )
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("--log-level=3")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(MAX_TIMEOUT)
        driver.set_script_timeout(MAX_TIMEOUT)
        try:
            driver.get(contact_url)
            # Use WebDriverWait instead of sleep
            WebDriverWait(driver, PAGE_LOAD_DELAY).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
        except Exception:
            # If timeout or no form found, continue with normal flow
            pass

        # Find all forms and filter intelligently
        forms = driver.find_elements(By.TAG_NAME, "form")
        main_forms = []

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

        # If still no forms found, use all forms as fallback
        if not main_forms:
            main_forms = [f for f in forms if not is_popup_or_newsletter_form(f)]

        if not main_forms:
            main_forms = forms  # Last resort: use all forms if none left

        def find_and_fill(possible_names, value):
            if not value:
                return False
            for form in main_forms:
                # Try by name, id, placeholder (contains, not just equals), but ignore search fields
                for name in possible_names:
                    # By name contains, but ignore search fields
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}') and not(contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search'))]",
                        )
                        if el.get_attribute("type") in [
                            None,
                            "",
                            "text",
                            "email",
                            "tel",
                            "number",
                            "password",
                        ] and not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                    # By id contains, but ignore search fields
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}') and not(contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search'))]",
                        )
                        if el.get_attribute("type") in [
                            None,
                            "",
                            "text",
                            "email",
                            "tel",
                            "number",
                            "password",
                        ] and not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                    # By placeholder contains, but ignore search fields
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}') and not(contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search'))]",
                        )
                        if el.get_attribute("type") in [
                            None,
                            "",
                            "text",
                            "email",
                            "tel",
                            "number",
                            "password",
                        ] and not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                # Try to match placeholder exactly to user field name (case-insensitive, ignore search fields)
                try:
                    inputs = form.find_elements(By.XPATH, ".//input")
                    for el in inputs:
                        placeholder = (
                            (el.get_attribute("placeholder") or "").strip().lower()
                        )
                        if placeholder and not "search" in placeholder:
                            for user_field in form_data:
                                # If the placeholder contains the user field name, or for email, if it contains 'email' anywhere (e.g. 'signup with email')
                                if (
                                    user_field in placeholder
                                    or (
                                        user_field == "email" and "email" in placeholder
                                    )
                                ) and form_data[user_field]:
                                    if el.is_displayed() and not el.get_attribute(
                                        "value"
                                    ):
                                        el.clear()
                                        el.send_keys(form_data[user_field])
                                        time.sleep(FILL_DELAY)
                                        return True
                except Exception:
                    pass
                # Try for partial match in any attribute, but ignore search fields
                try:
                    if value:
                        inputs = form.find_elements(By.XPATH, ".//input")
                        for el in inputs:
                            attrs = [
                                el.get_attribute("name") or "",
                                el.get_attribute("id") or "",
                                el.get_attribute("placeholder") or "",
                            ]
                            attrs = [a.lower() for a in attrs]
                            if any(
                                n in a for n in possible_names for a in attrs
                            ) and not any("search" in a for a in attrs):
                                if el.is_displayed() and not el.get_attribute("value"):
                                    el.clear()
                                    el.send_keys(value)
                                    time.sleep(FILL_DELAY)
                                    return True
                except Exception:
                    pass
                # Try textarea (no search bar issue for textarea)
                for name in possible_names:
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//textarea[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]",
                        )
                        if not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//textarea[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]",
                        )
                        if not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                    try:
                        el = form.find_element(
                            By.XPATH,
                            f".//textarea[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{name}')]",
                        )
                        if not el.get_attribute("value"):
                            el.clear()
                            el.send_keys(value)
                            time.sleep(FILL_DELAY)
                            return True
                    except Exception:
                        pass
                # As a last resort, try to fill any empty visible text input in main form, but ignore search fields
                try:
                    if value:
                        inputs = form.find_elements(
                            By.XPATH,
                            ".//input[@type='text' or @type='email' or @type='tel' or @type='number' or @type='password']",
                        )
                        for el in inputs:
                            attrs = [
                                el.get_attribute("name") or "",
                                el.get_attribute("id") or "",
                                el.get_attribute("placeholder") or "",
                            ]
                            attrs = [a.lower() for a in attrs]
                            if (
                                el.is_displayed()
                                and not el.get_attribute("value")
                                and not any("search" in a for a in attrs)
                            ):
                                el.clear()
                                el.send_keys(value)
                                time.sleep(FILL_DELAY)
                                return True
                except Exception:
                    pass
            return False

        # Use all collected user info for relevant fields
        find_and_fill(
            [
                "name",
                "your-name",
                "fullname",
                "full_name",
                "contactname",
                "contact_name",
            ],
            form_data["name"],
        )
        find_and_fill(
            [
                "email",
                "your-email",
                "mail",
                "contactemail",
                "contact_email",
                "contact[email]",
            ],
            form_data["email"],
        )
        filled_message = find_and_fill(
            [
                "message",
                "comment",
                "your-message",
                "enquiry",
                "query",
                "description",
                "body",
                "content",
            ],
            form_data["message"],
        )
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
        find_and_fill(
            [
                "phone",
                "mobile",
                "contactphone",
                "contact_phone",
                "phonenumber",
                "phone_number",
                "txtmobile",
            ],
            form_data.get("phone", ""),
        )
        find_and_fill(
            ["country", "your-country", "contactcountry", "contact_country"],
            form_data.get("country", ""),
        )
        find_and_fill(
            ["city", "your-city", "contactcity", "contact_city", "txtcity"],
            form_data.get("city", ""),
        )
        find_and_fill(
            ["state", "your-state", "contactstate", "contact_state"],
            form_data.get("state", ""),
        )
        find_and_fill(
            [
                "pincode",
                "pin",
                "zipcode",
                "zip",
                "postal",
                "postalcode",
                "postal_code",
                "txtpincode",
            ],
            form_data.get("pincode", ""),
        )
        find_and_fill(
            [
                "subject",
                "your-subject",
                "contactsubject",
                "contact_subject",
                "enquiry_subject",
                "txtsubject",
            ],
            form_data.get("subject", ""),
        )

        # Try to handle checkboxes and reCAPTCHA
        try:
            for form in main_forms:
                # Handle regular checkboxes first
                checkboxes = form.find_elements(By.XPATH, ".//input[@type='checkbox']")
                for checkbox in checkboxes:
                    # Look for common terms checkboxes by examining attributes and nearby text
                    checkbox_id = (checkbox.get_attribute("id") or "").lower()
                    checkbox_name = (checkbox.get_attribute("name") or "").lower()
                    checkbox_class = (checkbox.get_attribute("class") or "").lower()

                    # Try to get the label text if it exists
                    label_text = ""
                    try:
                        # Check for label using 'for' attribute
                        if checkbox_id:
                            label = form.find_element(
                                By.CSS_SELECTOR, f"label[for='{checkbox_id}']"
                            )
                            label_text = label.text.lower()
                    except:
                        # If no label found with 'for', try parent/sibling elements
                        try:
                            parent = checkbox.find_element(By.XPATH, "./..")
                            label_text = parent.text.lower()
                        except:
                            pass

                    # Keywords that suggest important checkboxes
                    important_keywords = [
                        "agree",
                        "accept",
                        "consent",
                        "confirm",
                        "privacy",
                        "policy",
                        "terms",
                        "conditions",
                        "required",
                        "human",
                        "robot",
                        "recaptcha",
                        "verify",
                        "newsletter",
                    ]

                    # Check if this is an important checkbox we should click
                    should_click = False
                    for keyword in important_keywords:
                        if (
                            keyword in checkbox_id
                            or keyword in checkbox_name
                            or keyword in checkbox_class
                            or keyword in label_text
                        ):
                            should_click = True
                            break

                    # Click the checkbox if it's important and not already checked
                    if (
                        should_click
                        and checkbox.is_displayed()
                        and checkbox.is_enabled()
                    ):
                        if not checkbox.is_selected():
                            try:
                                checkbox.click()
                                time.sleep(FILL_DELAY)
                            except:
                                # If direct click fails, try JavaScript click
                                try:
                                    driver.execute_script(
                                        "arguments[0].click();", checkbox
                                    )
                                    time.sleep(FILL_DELAY)
                                except:
                                    pass

            # Handle reCAPTCHA frames
            recaptcha_frames = driver.find_elements(
                By.XPATH, "//iframe[contains(@src, 'recaptcha')]"
            )
            for frame in recaptcha_frames:
                try:
                    driver.switch_to.frame(frame)
                    checkbox = driver.find_element(
                        By.CLASS_NAME, "recaptcha-checkbox-border"
                    )
                    if checkbox.is_displayed() and checkbox.is_enabled():
                        checkbox.click()
                        time.sleep(SUBMIT_DELAY)  # Give it time to verify
                    driver.switch_to.default_content()
                except Exception:
                    driver.switch_to.default_content()
                    continue

            # After handling checkboxes and reCAPTCHA, try to submit the form
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
                        time.sleep(SUBMIT_DELAY)  # Wait for submission to complete
                        break
                    except Exception:
                        continue
            except Exception:
                if driver is not None:
                    driver.quit()
                return False

        except Exception:
            pass

        # After submission, check for success indicators
        page_source = driver.page_source.lower()
        success_indicators = [
            "thank you",
            "success",
            "submitted",
            "we have received",
            "your message has been sent",
            "we will contact you",
            "form has been received",
        ]
        is_success = False
        for indicator in success_indicators:
            if indicator in page_source:
                is_success = True
                break
        # Always close the driver to free resources
        driver.quit()
        return is_success
    except Exception as e:
        # Make sure to close the driver in case of any exception
        if "driver" in locals() and driver is not None:
            driver.quit()
        return False


def is_popup_or_newsletter_form(form):
    """Check if a form is likely a popup or newsletter form"""
    try:
        # Get all form attributes
        form_id = (form.get_attribute("id") or "").lower()
        form_class = (form.get_attribute("class") or "").lower()
        form_html = form.get_attribute("outerHTML").lower()

        # Keywords that indicate popup/newsletter forms
        popup_indicators = [
            "popup",
            "modal",
            "newsletter",
            "subscribe",
            "sidebar",
            "overlay",
            "floating",
            "notification",
            "alert",
            "chat",
            "messenger",
            "livechat",
            "drift",
            "intercom",
            "zendesk",
            "cookie",
            "gdpr",
            "promotion",
            "offer",
            "discount",
            "sale",
            "signup",
            "login",
            "register",
        ]

        # Check form attributes for popup indicators
        for indicator in popup_indicators:
            if (
                indicator in form_id
                or indicator in form_class
                or indicator in form_html
            ):
                return True

        # Check form position/style
        style = form.get_attribute("style") or ""
        if (
            "position: fixed" in style
            or "position: absolute" in style
            or "z-index" in style
        ):
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
            "contact",
            "enquiry",
            "inquiry",
            "feedback",
            "support",
            "help-form",
            "contact-us",
            "get-in-touch",
            "reach-us",
            "write-to-us",
            "send-message",
        ]

        # Check for contact form indicators
        for indicator in contact_indicators:
            if (
                indicator in form_id
                or indicator in form_class
                or indicator in form_html
            ):
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


def click_relevant_checkboxes(form):
    """Click relevant checkboxes in the form"""
    try:
        # Important keywords that indicate required checkboxes
        important_keywords = [
            "agree",
            "accept",
            "consent",
            "confirm",
            "privacy",
            "policy",
            "terms",
            "conditions",
            "required",
            "human",
            "robot",
            "recaptcha",
            "verify",
            "newsletter",
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


websites = [
    # ...existing code...
]

form_data = {
    # ...existing code...
}

success_list = []
contact_not_found = []

for site in websites:
    print(f"\nChecking site: {site}")
    contact_url = find_contact_url(site)
    if contact_url:
        print(f"Found contact page: {contact_url}")
        result = fill_contact_form(contact_url, form_data)
        if result:
            print("✔️  Form submitted successfully.")
            success_list.append(site)
        else:
            print("Website didnt have form")
            contact_not_found.append(site)
    else:
        print("No contact page found.")
        contact_not_found.append(site)
    time.sleep(SWAP_DELAY)

# === RESULT ===
success_rate = (len(success_list) / len(websites)) * 100 if websites else 0
print("\n=== SUMMARY ===")
print("✅ Success:", success_list)
print("❌ Form Not Found:", contact_not_found)
print(f"📊 Success Rate: {success_rate:.2f}%")
