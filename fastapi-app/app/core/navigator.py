import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def find_contact_url(base_url):
    """Find the most likely contact page URL for a given website"""
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        base_url = "https://" + base_url

    # Check if the user provided a specific path (deep link)
    try:
        parsed_url = urlparse(base_url)
        is_deep_link = parsed_url.path and parsed_url.path not in ["/", ""]

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        response = session.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # If user provided a specific page and it HAS a form, assume this is the target
        if is_deep_link:
            if soup.find("form"):
                return base_url
        
        # If homepage has a form, it might be the target too, but prioritize contact page
        homepage_has_form = bool(soup.find("form"))
        
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
            "appointment": 5,
            "booking": 4,
        }

        links = soup.find_all("a", href=True)
        for link in links:
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
                try:
                    full_url = urljoin(base_url, href)
                    if full_url != base_url:
                        candidates.append((score, full_url))
                except:
                    continue
        
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
            
        # Fallback heuristic: Try checking common paths if scraping failed
        common_paths = ["/contact", "/contact-us", "/contactus", "/contact_us", "/enquiry"]
        for path in common_paths:
            try:
                test_url = urljoin(base_url, path)
                if test_url == base_url: continue
                
                # Verify if it exists (HEAD request)
                resp = session.head(test_url, timeout=3, allow_redirects=True)
                if resp.status_code == 200:
                    return test_url
            except:
                pass

        # If homepage has a form, assume it's valid
        if homepage_has_form:
            return base_url

        # As absolute last resort, return base_url
        return base_url
            
    except Exception:
        return base_url
