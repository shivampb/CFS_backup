from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# === CONFIGURATION ===
websites = [
    "https://freakins.com",
    "https://brillare.co.in",
    "https://dermalogica.in",
    "https://atmiyasurgical.com",
    "https://wishingoats.com",
    "https://maajisafashion.com",
    "https://beardo.in",
    "https://blackpoisontattoos.com",
    "https://indianclothstore.com",
    "https://yatradham.org",
    "https://outdoors91.com",
    "https://reneecosmetics.in"
    # Add more websites here
]

form_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "message": "Hello, I am interested in your service."
}

# === FIND CONTACT PAGE ===
def find_contact_url(base_url):
    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            link_text = link.text.strip().lower()
            link_href = link['href'].lower()
            if 'contact' in link_text or 'get in touch' in link_text or 'contact-us' in link_href:
                return link['href'] if 'http' in link['href'] else base_url.rstrip('/') + '/' + link['href'].lstrip('/')
    except:
        return None

# === FILL CONTACT FORM USING SELENIUM ===
def fill_contact_form(contact_url, form_data):
    try:
        driver = webdriver.Chrome()  # make sure chromedriver is installed and added to PATH
        driver.get(contact_url)
        time.sleep(3)

        # Try common field names — you can customize these
        try:
            driver.find_element(By.NAME, "name").send_keys(form_data["name"])
        except:
            pass
        try:
            driver.find_element(By.NAME, "email").send_keys(form_data["email"])
        except:
            pass
        try:
            driver.find_element(By.NAME, "message").send_keys(form_data["message"])
        except:
            pass

        # Try clicking the submit button
        try:
            submit_button = driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']")
            submit_button.click()
        except:
            driver.quit()
            return False

        time.sleep(2)
        driver.quit()
        return True
    except:
        return False

# === MAIN LOGIC ===
success_list = []
Contact_Not_found = []

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
        Contact_Not_found.append(site)

# === RESULT ===
success_rate = (len(success_list) / len(websites)) * 100 if websites else 0
print("\n=== SUMMARY ===")
print("✅ Success:", success_list)
print("❌ Form Not Found:", Contact_Not_found)
print(f"📊 Success Rate: {success_rate:.2f}%")
