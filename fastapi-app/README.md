# Contact Form Submitter - Usage Guide

## Overview
This application automates the process of finding and submitting contact forms on multiple websites. It handles dynamic content, popups, and various form structures intelligently.

## Features
- **Smart Navigation**: Finds contact pages even on single-page apps.
- **Direct URL Support**: Accepts specific page URLs (e.g., `example.com/landing`) and processes them directly if they contain a form.
- **Dynamic Form Filling**: populates inputs, textareas, and dropdowns.
- **Popup Handling**: Closes cookie banners and promotional popups.
- **Resilience**: Randomly fills optional fields to ensure submission.
- **Parallel Processing**: fast operation with multi-threading.

## Running the Application

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access the Dashboard**:
   Open your browser to: `http://127.0.0.1:8000`

## Structure
- `app/core/`: proper modular logic (engine, browser, navigator, form_filler).
- `app/templates/`: HTML frontend.
