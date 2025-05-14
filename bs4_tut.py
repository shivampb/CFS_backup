from bs4 import BeautifulSoup
import requests

def find_contact_url(base_url):
    try:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            link_text = link.text.strip().lower()
            link_href = link['href'].lower()
            if 'contact' in link_text or 'get in touch' in link_text or 'contact' in link_href:
                return link['href'] if 'http' in link['href'] else base_url.rstrip('/') + '/' + link['href'].lstrip('/')
    except:
        return None

print(find_contact_url("https://snackible.com/"))
print(find_contact_url("https://www.anandsweets.in/"))
