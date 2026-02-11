import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def find_contact_url(base_url):
    """Find the most likely contact page URL for a given website"""
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        base_url = "https://" + base_url

    try:
        # Check if the user provided a specific path (deep link)
        parsed_url = urlparse(base_url)
        is_deep_link = parsed_url.path and parsed_url.path != "/"

        response = requests.get(base_url, timeout=3)
        soup = BeautifulSoup(response.text, "html.parser")

        # If user provided a specific page and it HAS a form, assume this is the target
        if is_deep_link:
            if soup.find("form"):
                return base_url
        
        candidates = []
        
        # Keywords with weights for scoring
        keywords = {
            "contact us": 10,
            "contact": 8,
            "get in touch": 7,
            "reach us": 6,
            "write to us": 6,
            "support": 4,
            "help": 2,
            "enquiry": 5,
            "inquiry": 5,
            "feedback": 3,
        }

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            text = link.text.strip().lower()
            
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
                
            score = 0
            href_lower = href.lower()
            
            # Check for exact matches first for high confidence
            if href_lower.endswith("/contact") or href_lower.endswith("/contact-us") or href_lower == "contact":
                score += 15
            
            for key, weight in keywords.items():
                if key in text:
                    score += weight
                if key in href_lower:
                    score += weight
            
            if score > 0:
                # Construct full URL securely
                try:
                    full_url = urljoin(base_url, href)
                    # Exclude same page anchors
                    if full_url != base_url:
                        candidates.append((score, full_url))
                except:
                    continue
        
        if candidates:
            # Return the highest scoring URL
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
            
        # If no explicit contact page found, return base_url 
        # (the form might be on the homepage itself, e.g. landing pages)
        return base_url
            
    except Exception:
        # On error (e.g. timeout), return base_url to let Selenium try
        return base_url
