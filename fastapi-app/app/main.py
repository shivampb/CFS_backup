import logging
from fastapi import FastAPI, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.contact import find_contact_url, fill_contact_form, process_websites
from app.database import get_db, engine
from app.models import Base, User
from app import auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS - Updated configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")


# Authentication endpoints
@app.post("/api/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Received registration request for username: {username}, email: {email}"
    )
    try:
        # Check if user exists
        if db.query(User).filter(User.email == email).first():
            logger.warning(f"Registration failed: Email already registered - {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        if db.query(User).filter(User.username == username).first():
            logger.warning(f"Registration failed: Username already taken - {username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        # Create new user
        hashed_password = auth.get_password_hash(password)
        user = User(username=username, email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create access token
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        logger.info(f"User registered successfully: {username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Registration failed with error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@app.post("/api/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@app.get("/api/me")
async def read_users_me(current_user: User = Depends(auth.get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }


# Existing routes
@app.api_route("/", methods=["GET", "POST"], response_class=HTMLResponse)
async def main_form(request: Request):
    if request.method == "GET":
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "success_list": [],
                "contact_not_found": [],
                "contact_not_found_count": 0,
                "success_rate": None,
                # Clear all form fields on refresh
                "websites": "",
                "name": "",
                "email": "",
                "message": "",
                "phone": "",
                "country": "",
                "city": "",
                "state": "",
                "pincode": "",
            },
        )
    form = await request.form()
    websites = form.get("websites", "")
    name = form.get("name", "")
    email = form.get("email", "")
    message = form.get("message", "")
    phone = form.get("phone", "")
    country = form.get("country", "")
    city = form.get("city", "")
    state = form.get("state", "")
    pincode = form.get("pincode", "")
    subject = form.get("subject", "")
    websites_list = [w.strip() for w in websites.splitlines() if w.strip()]
    if not websites_list:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "success_list": [],
                "contact_not_found": [],
                "contact_not_found_count": 0,
                "success_rate": None,
                "error": "Please enter at least one website URL.",
                "websites": websites,
                "name": name,
                "email": email,
                "message": message,
                "phone": phone,
                "country": country,
                "city": city,
                "state": state,
                "pincode": pincode,
            },
        )
    form_data = {
        "name": name.strip(),
        "email": email.strip(),
        "message": message.strip(),
        "phone": phone.strip(),
        "country": country.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "pincode": pincode.strip(),
        "subject": subject.strip(),
    }
    # Process websites in parallel
    success_list, contact_not_found = process_websites(websites_list, form_data)
    total_sites = len(websites_list)
    success_rate = (len(success_list) / total_sites) * 100 if total_sites else 0
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "success_list": success_list,
            "contact_not_found": contact_not_found,
            "contact_not_found_count": len(contact_not_found),
            "success_rate": f"{success_rate:.2f}",
            # Clear all form fields after POST/refresh
            "websites": "",
            "name": "",
            "email": "",
            "message": "",
            "phone": "",
            "country": "",
            "city": "",
            "state": "",
            "pincode": "",
        },
    )
