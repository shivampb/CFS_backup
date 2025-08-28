import threading
import time
from queue import Queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
import requests
from urllib.parse import urljoin

# ==== CONFIGURABLE DETAILS ====
my_form_data = {
    "name": "Shivam Bhardwaj",
    "email": "business@destinovaailabs.com",
    "phone": "+91 7041083626",
    "message": "Hello, I wanted to reach out regarding potential collaboration opportunities.",
}

urls = [
    "https://shivamtestsite.netlify.app/",
    "https://miir.com",
    "https://vitalityextracts.com",
]

NUM_THREADS = 5
results = {}


# ==== BROWSER SETUP ====
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=chrome_options)


# ==== CORE FUNCTION ====
def process_site(url):
    driver = None
    try:
        driver = get_driver()
        driver.set_page_load_timeout(20)
        driver.get(url)

        # Step 1: Try to locate contact page link in footer
        contact_link = None
        footer_links = driver.find_elements(By.TAG_NAME, "a")
        for link in footer_links:
            href = link.get_attribute("href")
            if href and ("contact" in href.lower()):
                contact_link = href
                break

        if not contact_link:
            results[url] = "Failed - No Contact Page"
            return

        # Step 2: Open contact page
        driver.get(contact_link)
        time.sleep(2)

        # Step 3: Find form
        form = driver.find_element(By.TAG_NAME, "form")
        inputs = form.find_elements(By.TAG_NAME, "input") + form.find_elements(
            By.TAG_NAME, "textarea"
        )

        # Step 4: Fill fields (smart-matching based on name/id/placeholder)
        for field in inputs:
            field_type = (
                field.get_attribute("name")
                or field.get_attribute("id")
                or field.get_attribute("placeholder")
                or ""
            ).lower()
            if "name" in field_type:
                field.send_keys(my_form_data["name"])
            elif "mail" in field_type:
                field.send_keys(my_form_data["email"])
            elif "phone" in field_type or "mobile" in field_type:
                field.send_keys(my_form_data["phone"])
            elif (
                "message" in field_type
                or "comment" in field_type
                or "enquiry" in field_type
            ):
                field.send_keys(my_form_data["message"])

        # Step 5: Submit form
        try:
            submit_button = form.find_element(
                By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
            )
            submit_button.click()
        except NoSuchElementException:
            results[url] = "Failed - No Submit Button"
            return

        # Step 6: Handle captcha (basic - just try clicking if visible)
        try:
            captcha = driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            driver.switch_to.frame(captcha)
            driver.find_element(By.CLASS_NAME, "recaptcha-checkbox").click()
            driver.switch_to.default_content()
            time.sleep(2)
        except NoSuchElementException:
            pass  # No captcha

        results[url] = "Done ✅"

    except (NoSuchElementException, TimeoutException, WebDriverException) as e:
        results[url] = f"Failed - {str(e)[:40]}"
    finally:
        if driver:
            driver.quit()


# ==== MULTI-THREADING ====
def worker(q):
    while not q.empty():
        site = q.get()
        process_site(site)
        q.task_done()


def main():
    q = Queue()
    for u in urls:
        q.put(u)

    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(q,))
        t.start()
        threads.append(t)

    q.join()
    for t in threads:
        t.join()

    print("\n--- Results ---")
    for site, status in results.items():
        print(f"{site}: {status}")


if __name__ == "__main__":
    main()
