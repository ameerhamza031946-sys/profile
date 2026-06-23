# =============================================================================
#   AMEER HAMZA — PORTFOLIO BACKEND (Single File)
#   FastAPI + MongoDB (Motor)
#   Run: pip install fastapi uvicorn motor pydantic-settings pydantic[email] python-multipart
#   Start: uvicorn portfolio_backend:app --reload
# =============================================================================

import os
import shutil
import uuid
import smtplib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Annotated

import jwt
import bcrypt
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks, FastAPI, File, HTTPException, UploadFile, status, Depends, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field, ConfigDict, BeforeValidator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# =============================================================================
#  CONFIGURATION & SECURITY SETUP
# =============================================================================

load_dotenv()

MONGO_URL      = os.getenv("MONGO_URL", "mongodb://localhost:27017")
SECRET_KEY     = os.getenv("SECRET_KEY", "super-secret-key-12345")
ALGORITHM      = "HS256"
TOKEN_EXPIRY   = 1440 # 24 hours

SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASS      = os.getenv("SMTP_PASS", "")
OWNER_EMAIL    = os.getenv("OWNER_EMAIL", "ameerhamza031946@gmail.com")

CLIENT = AsyncIOMotorClient(MONGO_URL)
DB = CLIENT["portfolio_db"]

# Collections
COL_CONTACTS       = DB["contact_messages"]
COL_PROJECTS       = DB["projects"]
COL_SKILLS         = DB["skills"]
COL_CERTIFICATIONS = DB["certifications"]
COL_PROFILE        = DB["profile"]
COL_ADMINS         = DB["admins"]

# Security Tools
def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
limiter = Limiter(key_func=get_remote_address)

# Helper to handle MongoDB ObjectId in Pydantic
PyObjectId = Annotated[str, BeforeValidator(str)]

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

# ── Auth ───────────────────────────────────────────────────────────────────

class AdminCreate(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_admin(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    admin = await COL_ADMINS.find_one({"username": username})
    if admin is None:
        raise credentials_exception
    return admin

# ── Contact ────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class ContactResponse(MongoBaseModel):
    name: str
    email: str
    subject: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ContactUpdate(BaseModel):
    is_read: Optional[bool] = None

# ── Project ────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: str
    tech_stack: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_featured: bool = False
    order_index: int = 0

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_featured: Optional[bool] = None
    order_index: Optional[int] = None

class ProjectResponse(MongoBaseModel):
    title: str
    description: str
    tech_stack: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_featured: bool = False
    order_index: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ── Skill ──────────────────────────────────────────────────────────────────

class SkillCreate(BaseModel):
    name: str
    percentage: float
    category: Optional[str] = "Technical"
    icon: Optional[str] = None
    order_index: int = 0

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    percentage: Optional[float] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    order_index: Optional[int] = None

class SkillResponse(MongoBaseModel):
    name: str
    percentage: float
    category: Optional[str] = None
    icon: Optional[str] = None
    order_index: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ── Certification ──────────────────────────────────────────────────────────

class CertificationCreate(BaseModel):
    badge_number: Optional[str] = None
    issuer: str
    name: str
    date_info: Optional[str] = None
    registration_number: Optional[str] = None
    description: Optional[str] = None
    certificate_url: Optional[str] = None
    order_index: int = 0

class CertificationUpdate(BaseModel):
    badge_number: Optional[str] = None
    issuer: Optional[str] = None
    name: Optional[str] = None
    date_info: Optional[str] = None
    registration_number: Optional[str] = None
    description: Optional[str] = None
    certificate_url: Optional[str] = None
    order_index: Optional[int] = None

class CertificationResponse(MongoBaseModel):
    badge_number: Optional[str] = None
    issuer: str
    name: str
    date_info: Optional[str] = None
    registration_number: Optional[str] = None
    description: Optional[str] = None
    certificate_url: Optional[str] = None
    order_index: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ── Profile ────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    father_name: Optional[str] = None
    title: Optional[str] = None
    tagline: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    roll_no: Optional[str] = None
    bano_qabil_id: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    photo_url: Optional[str] = None
    resume_url: Optional[str] = None
    years_experience: Optional[int] = None
    projects_count: Optional[int] = None

class ProfileResponse(MongoBaseModel):
    full_name: str
    father_name: Optional[str] = None
    title: Optional[str] = None
    tagline: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    roll_no: Optional[str] = None
    bano_qabil_id: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    photo_url: Optional[str] = None
    resume_url: Optional[str] = None
    years_experience: Optional[int] = 0
    projects_count: Optional[int] = 0

# =============================================================================
#  ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗
# ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝
# ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗
# ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║
# ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝
#  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝
# =============================================================================

# Credentials loaded from .env above

import logging
logger = logging.getLogger("uvicorn.error")

def send_email_notification(name: str, email: str, subject: str, message: str):
    logger.info(f"EMAIL TASK STARTED: From {name} ({email})")
    if not SMTP_USER:
        logger.warning("WARNING: SMTP_USER not set - email skipped")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"New Portfolio Message: {subject}"
        msg["From"]    = SMTP_USER
        msg["To"]      = OWNER_EMAIL

        html_body = f"""
        <html><body style="font-family:Arial;background:#0a0a0a;color:#f0ede6;padding:30px;">
            <h2 style="color:#c8f53c;">New Contact Message</h2>
            <table style="border-collapse:collapse;width:100%;">
                <tr><td style="padding:8px;color:#888;">Name</td>
                    <td style="padding:8px;">{name}</td></tr>
                <tr><td style="padding:8px;color:#888;">Email</td>
                    <td style="padding:8px;">{email}</td></tr>
                <tr><td style="padding:8px;color:#888;">Subject</td>
                    <td style="padding:8px;">{subject}</td></tr>
            </table>
            <hr style="border-color:#222;margin:20px 0;"/>
            <p style="color:#888;">Message:</p>
            <p style="background:#181818;padding:16px;border-left:3px solid #c8f53c;">{message}</p>
        </body></html>
        """
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            clean_pass = SMTP_PASS.replace(" ", "").strip()
            server.login(SMTP_USER, clean_pass)
            server.sendmail(SMTP_USER, OWNER_EMAIL, msg.as_string())
        logger.info(f"OK: Email sent for message from {name}")
    except Exception as e:
        logger.error(f"Error: Email send failed: {e}")

def send_auto_reply(name: str, email: str, subject: str):
    logger.info(f"AUTO REPLY TASK STARTED: To {name} ({email})")
    if not SMTP_USER:
        logger.warning("WARNING: SMTP_USER not set - auto reply skipped")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Thank you for reaching out! - Ameer Hamza"
        msg["From"]    = SMTP_USER
        msg["To"]      = email

        html_body = f"""
        <html><body style="font-family:Arial;background:#0a0a0a;color:#f0ede6;padding:30px;">
            <h2 style="color:#c8f53c;">Hello {name},</h2>
            <p>Thank you for getting in touch! I have received your message regarding <strong>"{subject}"</strong>.</p>
            <p>I will review your message and get back to you as soon as possible.</p>
            <hr style="border-color:#222;margin:20px 0;"/>
            <p style="color:#888;font-size:12px;">This is an automated confirmation email. Please do not reply directly to this message.</p>
            <p style="color:#c8f53c;font-weight:bold;">Best regards,<br>Ameer Hamza</p>
        </body></html>
        """
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            clean_pass = SMTP_PASS.replace(" ", "").strip()
            server.login(SMTP_USER, clean_pass)
            server.sendmail(SMTP_USER, email, msg.as_string())
        logger.info(f"OK: Auto reply email sent to {email}")
    except Exception as e:
        logger.error(f"Error: Auto reply email send failed: {e}")

# =============================================================================
#  █████╗ ██████╗ ██████╗
# ██╔══██╗██╔══██╗██╔══██╗
# ███████║██████╔╝██████╔╝
# ██╔══██║██╔═══╝ ██╔═══╝
# ██║  ██║██║     ██║
# ╚═╝  ╚═╝╚═╝     ╚═╝
# =============================================================================

DEFAULT_SKILLS = [
    {"name": "Python",           "percentage": 85, "category": "Technical",        "order_index": 1, "created_at": datetime.utcnow()},
    {"name": "Machine Learning", "percentage": 78, "category": "AI/ML",            "order_index": 2, "created_at": datetime.utcnow()},
    {"name": "Data Analysis",    "percentage": 80, "category": "AI/ML",            "order_index": 3, "created_at": datetime.utcnow()},
    {"name": "HTML / CSS",       "percentage": 75, "category": "Web",              "order_index": 4, "created_at": datetime.utcnow()},
    {"name": "Computer Vision",  "percentage": 65, "category": "AI/ML",            "order_index": 5, "created_at": datetime.utcnow()},
    {"name": "AI Applications",  "percentage": 72, "category": "AI/ML",            "order_index": 6, "created_at": datetime.utcnow()},
]

DEFAULT_CERTS = [
    {
        "badge_number": "01",
        "issuer": "Government Vocational Institute · Govt of Sindh",
        "name": "Advance Computer Information Technology (ACIT)",
        "date_info": "Aug 2024 – Jan 2025",
        "registration_number": "GVI/ACIT/319",
        "description": "Successfully completed ACIT course at Government Vocational Institute, Affandi Town, Hyderabad.",
        "order_index": 1,
        "created_at": datetime.utcnow(),
    },
    {
        "badge_number": "02",
        "issuer": "Tech Pakistan · Ministry of IT & Telecom",
        "name": "AI Hackathon — Indus AI Week 2026",
        "date_info": "2026 · Indus AI Week",
        "description": "Certificate of active participation in the AI Hackathon during Indus AI Week 2026, organized by Tech Pakistan, Saylani, NIC, and Govt of Sindh.",
        "order_index": 2,
        "created_at": datetime.utcnow(),
    },

]

async def seed_default_data():
    if await COL_PROFILE.count_documents({}) == 0:
        await COL_PROFILE.insert_one({
            "full_name": "Ameer Hamza",
            "father_name": "Muhammad Zubair",
            "title": "AI & Data Science Developer",
            "tagline": "Building intelligent solutions with Python, ML & AI",
            "bio": "I'm Ameer Hamza, an ambitious AI & Data Science student from Hyderabad, Sindh. I am currently enrolled at Saylani Mass IT Training (SMIT) in the Artificial Intelligence and Data Science track.",
            "email": "ameerhamza031946@gmail.com",
            "phone": "0319-4613960",
            "location": "Hyderabad, Sindh, Pakistan",
            "province": "Sindh",
            "city": "Hyderabad",
            "roll_no": "AI-457375",
            "bano_qabil_id": "1366690",
            "years_experience": 1,
            "projects_count": 5,
        })

    if await COL_SKILLS.count_documents({}) == 0:
        await COL_SKILLS.insert_many(DEFAULT_SKILLS)

    if await COL_CERTIFICATIONS.count_documents({}) == 0:
        await COL_CERTIFICATIONS.insert_many(DEFAULT_CERTS)

    if await COL_ADMINS.count_documents({}) == 0:
        hashed_pass = get_password_hash("admin123")
        await COL_ADMINS.insert_one({"username": "admin", "password_hash": hashed_pass})
        print("INFO: Default admin created (admin / admin123)")

    print("OK: MongoDB default seed data inserted!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("uploads/projects", exist_ok=True)
    os.makedirs("uploads/profile",  exist_ok=True)
    await seed_default_data()
    print("START: Ameer Hamza Portfolio API — Ready!")
    yield
    print("INFO: API shutting down...")

app = FastAPI(
    title="Ameer Hamza — Portfolio API (Secure)",
    description="Backend API with JWT Auth, Rate Limiting, and MongoDB security.",
    version="1.2.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# =============================================================================
# ██████╗  ██████╗ ██╗   ██╗████████╗███████╗███████╗
# ██╔══██╗██╔═══██╗██║   ██║╚══██╔══╝██╔════╝██╔════╝
# ██████╔╝██║   ██║██║   ██║   ██║   █████╗  ███████╗
# ██╔══██╗██║   ██║██║   ██║   ██║   ██╔══╝  ╚════██║
# ██║  ██║╚██████╔╝╚██████╔╝   ██║   ███████╗███████║
# ╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝╚══════╝
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to Ameer Hamza Portfolio API (MongoDB)", "docs": "/docs"}

@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok", "message": "MongoDB connected"}

# ── Auth ───────────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(data: LoginRequest):
    admin = await COL_ADMINS.find_one({"username": data.username})
    if not admin or not verify_password(data.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": admin["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ── Contact ────────────────────────────────────────────────────────────────

@app.post("/api/contact", response_model=ContactResponse, status_code=201, tags=["Contact"])
@limiter.limit("5/minute")
async def send_message(request: Request, data: ContactCreate, background_tasks: BackgroundTasks):
    msg_dict = data.model_dump()
    msg_dict["is_read"] = False
    msg_dict["created_at"] = datetime.utcnow()
    res = await COL_CONTACTS.insert_one(msg_dict)
    msg_dict["_id"] = res.inserted_id
    background_tasks.add_task(send_email_notification, data.name, data.email, data.subject, data.message)
    background_tasks.add_task(send_auto_reply, data.name, data.email, data.subject)
    return msg_dict

@app.get("/api/contact", response_model=List[ContactResponse], tags=["Contact"])
async def get_messages(current_admin: Annotated[dict, Depends(get_current_admin)], skip: int = 0, limit: int = 50, unread_only: bool = False):
    filt = {"is_read": False} if unread_only else {}
    cursor = COL_CONTACTS.find(filt).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

@app.get("/api/contact/{message_id}", response_model=ContactResponse, tags=["Contact"])
async def get_message(message_id: str, current_admin: Annotated[dict, Depends(get_current_admin)]):
    msg = await COL_CONTACTS.find_one({"_id": ObjectId(message_id)})
    if not msg: raise HTTPException(404, "Message nahi mila")
    return msg

@app.patch("/api/contact/{message_id}", response_model=ContactResponse, tags=["Contact"])
async def mark_message(message_id: str, data: ContactUpdate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    upd = data.model_dump(exclude_unset=True)
    res = await COL_CONTACTS.find_one_and_update(
        {"_id": ObjectId(message_id)}, {"$set": upd}, return_document=True
    )
    if not res: raise HTTPException(404, "Message nahi mila")
    return res

@app.delete("/api/contact/{message_id}", status_code=204, tags=["Contact"])
async def delete_message(message_id: str, current_admin: Annotated[dict, Depends(get_current_admin)]):
    res = await COL_CONTACTS.delete_one({"_id": ObjectId(message_id)})
    if res.deleted_count == 0: raise HTTPException(404, "Message nahi mila")

# ── Projects ───────────────────────────────────────────────────────────────

@app.get("/api/projects", response_model=List[ProjectResponse], tags=["Projects"])
async def get_projects(category: Optional[str] = None, featured_only: bool = False, skip: int = 0, limit: int = 20):
    filt = {}
    if category: filt["category"] = category
    if featured_only: filt["is_featured"] = True
    cursor = COL_PROJECTS.find(filt).sort([("order_index", 1), ("created_at", -1)]).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

@app.get("/api/projects/featured", response_model=List[ProjectResponse], tags=["Projects"])
async def get_featured_projects():
    cursor = COL_PROJECTS.find({"is_featured": True}).sort("order_index", 1)
    return await cursor.to_list(length=50)

@app.get("/api/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def get_project(project_id: str):
    p = await COL_PROJECTS.find_one({"_id": ObjectId(project_id)})
    if not p: raise HTTPException(404, "Project nahi mila")
    return p

@app.post("/api/projects", response_model=ProjectResponse, status_code=201, tags=["Projects"])
async def create_project(data: ProjectCreate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    p_dict = data.model_dump()
    p_dict["created_at"] = datetime.utcnow()
    res = await COL_PROJECTS.insert_one(p_dict)
    p_dict["_id"] = res.inserted_id
    return p_dict

@app.put("/api/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def update_project(project_id: str, data: ProjectUpdate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    upd = data.model_dump(exclude_unset=True)
    res = await COL_PROJECTS.find_one_and_update(
        {"_id": ObjectId(project_id)}, {"$set": upd}, return_document=True
    )
    if not res: raise HTTPException(404, "Project nahi mila")
    return res

@app.delete("/api/projects/{project_id}", status_code=204, tags=["Projects"])
async def delete_project(project_id: str, current_admin: Annotated[dict, Depends(get_current_admin)]):
    res = await COL_PROJECTS.delete_one({"_id": ObjectId(project_id)})
    if res.deleted_count == 0: raise HTTPException(404, "Project nahi mila")

@app.post("/api/projects/{project_id}/upload-image", tags=["Projects"])
async def upload_project_image(project_id: str, current_admin: Annotated[dict, Depends(get_current_admin)], file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        raise HTTPException(400, "Sirf images allowed hain")
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = f"uploads/projects/{filename}"
    with open(path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    res = await COL_PROJECTS.update_one({"_id": ObjectId(project_id)}, {"$set": {"image_url": f"/uploads/projects/{filename}"}})
    if res.matched_count == 0: raise HTTPException(404, "Project nahi mila")
    return {"message": "Image uploaded", "image_url": f"/uploads/projects/{filename}"}

# ── Skills ─────────────────────────────────────────────────────────────────

@app.get("/api/skills", response_model=List[SkillResponse], tags=["Skills"])
async def get_skills(category: Optional[str] = None):
    filt = {"category": category} if category else {}
    cursor = COL_SKILLS.find(filt).sort([("order_index", 1), ("percentage", -1)])
    return await cursor.to_list(length=100)

@app.get("/api/skills/{skill_id}", response_model=SkillResponse, tags=["Skills"])
async def get_skill(skill_id: str):
    s = await COL_SKILLS.find_one({"_id": ObjectId(skill_id)})
    if not s: raise HTTPException(404, "Skill nahi mili")
    return s

@app.post("/api/skills", response_model=SkillResponse, status_code=201, tags=["Skills"])
async def create_skill(data: SkillCreate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    s_dict = data.model_dump()
    s_dict["created_at"] = datetime.utcnow()
    res = await COL_SKILLS.insert_one(s_dict)
    s_dict["_id"] = res.inserted_id
    return s_dict

@app.post("/api/skills/bulk", response_model=List[SkillResponse], status_code=201, tags=["Skills"])
async def bulk_create_skills(skills_data: List[SkillCreate], current_admin: Annotated[dict, Depends(get_current_admin)]):
    docs = []
    for s in skills_data:
        d = s.model_dump()
        d["created_at"] = datetime.utcnow()
        docs.append(d)
    res = await COL_SKILLS.insert_many(docs)
    for i, doc in enumerate(docs): doc["_id"] = res.inserted_ids[i]
    return docs

@app.put("/api/skills/{skill_id}", response_model=SkillResponse, tags=["Skills"])
async def update_skill(skill_id: str, data: SkillUpdate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    upd = data.model_dump(exclude_unset=True)
    res = await COL_SKILLS.find_one_and_update({"_id": ObjectId(skill_id)}, {"$set": upd}, return_document=True)
    if not res: raise HTTPException(404, "Skill nahi mili")
    return res

@app.delete("/api/skills/{skill_id}", status_code=204, tags=["Skills"])
async def delete_skill(skill_id: str, current_admin: Annotated[dict, Depends(get_current_admin)]):
    res = await COL_SKILLS.delete_one({"_id": ObjectId(skill_id)})
    if res.deleted_count == 0: raise HTTPException(404, "Skill nahi mili")

# ── Certifications ─────────────────────────────────────────────────────────

@app.get("/api/certifications", response_model=List[CertificationResponse], tags=["Certifications"])
async def get_certifications():
    cursor = COL_CERTIFICATIONS.find({}).sort("order_index", 1)
    return await cursor.to_list(length=100)

@app.get("/api/certifications/{cert_id}", response_model=CertificationResponse, tags=["Certifications"])
async def get_certification(cert_id: str):
    c = await COL_CERTIFICATIONS.find_one({"_id": ObjectId(cert_id)})
    if not c: raise HTTPException(404, "Certificate nahi mila")
    return c

@app.post("/api/certifications", response_model=CertificationResponse, status_code=201, tags=["Certifications"])
async def create_certification(data: CertificationCreate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    c_dict = data.model_dump()
    c_dict["created_at"] = datetime.utcnow()
    res = await COL_CERTIFICATIONS.insert_one(c_dict)
    c_dict["_id"] = res.inserted_id
    return c_dict

@app.put("/api/certifications/{cert_id}", response_model=CertificationResponse, tags=["Certifications"])
async def update_certification(cert_id: str, data: CertificationUpdate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    upd = data.model_dump(exclude_unset=True)
    res = await COL_CERTIFICATIONS.find_one_and_update({"_id": ObjectId(cert_id)}, {"$set": upd}, return_document=True)
    if not res: raise HTTPException(404, "Certificate nahi mila")
    return res

@app.delete("/api/certifications/{cert_id}", status_code=204, tags=["Certifications"])
async def delete_certification(cert_id: str, current_admin: Annotated[dict, Depends(get_current_admin)]):
    res = await COL_CERTIFICATIONS.delete_one({"_id": ObjectId(cert_id)})
    if res.deleted_count == 0: raise HTTPException(404, "Certificate nahi mila")

# ── Profile ────────────────────────────────────────────────────────────────

async def _get_or_create_profile() -> dict:
    p = await COL_PROFILE.find_one({})
    if not p:
        p = {
            "full_name": "Ameer Hamza",
            "father_name": "Muhammad Zubair",
            "title": "AI & Data Science Developer",
            "tagline": "Building intelligent solutions with Python, ML & AI",
            "bio": "I'm Ameer Hamza, an ambitious AI & Data Science student from Hyderabad, Sindh. I am currently enrolled at Saylani Mass IT Training (SMIT) in the Artificial Intelligence and Data Science track.",
            "email": "ameerhamza031946@gmail.com",
            "phone": "0319-4613960",
            "location": "Hyderabad, Sindh, Pakistan",
            "province": "Sindh",
            "city": "Hyderabad",
            "roll_no": "AI-457375",
            "bano_qabil_id": "1366690",
            "years_experience": 1,
            "projects_count": 5,
        }
        res = await COL_PROFILE.insert_one(p)
        p["_id"] = res.inserted_id
    return p

@app.get("/api/profile", response_model=ProfileResponse, tags=["Profile"])
async def get_profile():
    return await _get_or_create_profile()

@app.put("/api/profile", response_model=ProfileResponse, tags=["Profile"])
async def update_profile(data: ProfileUpdate, current_admin: Annotated[dict, Depends(get_current_admin)]):
    upd = data.model_dump(exclude_unset=True)
    await _get_or_create_profile() 
    res = await COL_PROFILE.find_one_and_update({}, {"$set": upd}, return_document=True)
    return res

@app.post("/api/profile/upload-photo", tags=["Profile"])
async def upload_profile_photo(current_admin: Annotated[dict, Depends(get_current_admin)], file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(400, "Sirf images allowed hain")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024: raise HTTPException(400, "File too large")
    ext = file.filename.split(".")[-1]
    filename = f"profile_{uuid.uuid4().hex[:8]}.{ext}"
    path = f"uploads/profile/{filename}"
    with open(path, "wb") as f: f.write(contents)
    await COL_PROFILE.update_one({}, {"$set": {"photo_url": f"/uploads/profile/{filename}"}})
    return {"message": "Photo uploaded", "photo_url": f"/uploads/profile/{filename}"}

@app.get("/api/profile/stats", tags=["Profile"])
async def get_stats():
    return {
        "total_projects": await COL_PROJECTS.count_documents({}),
        "featured_projects": await COL_PROJECTS.count_documents({"is_featured": True}),
        "total_skills": await COL_SKILLS.count_documents({}),
        "total_certs": await COL_CERTIFICATIONS.count_documents({}),
        "total_messages": await COL_CONTACTS.count_documents({}),
        "unread_messages": await COL_CONTACTS.count_documents({"is_read": False}),
    }
