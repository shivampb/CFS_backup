# FastAPI Contact App

This project is a FastAPI application that allows users to submit contact forms to various websites. It scrapes the websites for contact pages and fills out the forms using Selenium. The results of the submissions are displayed on the frontend.

## Project Structure

```
fastapi-contact-app
├── app
│   ├── main.py          # Entry point of the FastAPI application
│   ├── contact.py       # Logic for finding contact pages and filling out forms
│   └── templates
│       └── index.html   # HTML template for the frontend
├── requirements.txt      # List of dependencies
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd fastapi-contact-app
   ```

2. **Create a virtual environment** (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```
   uvicorn app.main:app --reload
   ```

5. **Access the application**:
   Open your browser and go to `http://127.0.0.1:8000`.

## Usage

- Navigate to the homepage where you will find a form to input your name, email, and message.
- Upon submission, the application will attempt to find contact pages on the specified websites and fill out the forms.
- The results will be displayed on the same page, showing which submissions were successful and which contact forms were not found.

## Required Dependencies

- fastapi
- uvicorn
- beautifulsoup4
- requests
- selenium
- jinja2

Make sure to install all the required dependencies listed in `requirements.txt` before running the application.