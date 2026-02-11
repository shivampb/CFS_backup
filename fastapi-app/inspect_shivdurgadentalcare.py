import requests
from bs4 import BeautifulSoup

url = "https://shivdurgadentalcare.com/contact/"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

forms = soup.find_all('form')
for i, form in enumerate(forms):
    print(f"--- Form {i+1} ---")
    # Print the form's HTML (prettified)
    print(form.prettify())
    print("\n")
