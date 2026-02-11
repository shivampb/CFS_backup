from app.core.engine import process_website

# Test data
site = "http://shivdurgadentalcare.com/"
form_data = {
    "name": "Test User",
    "email": "test@example.com",
    "message": "This is a test message to check form submission.",
    "phone": "9876543210",
    "country": "India",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "subject": "Inquiry"
}

print(f"Testing site: {site}")
result = process_website(site, form_data)
print(f"Result: {result}")
