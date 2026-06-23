import pymongo
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
CLIENT = pymongo.MongoClient(MONGO_URL)
DB = CLIENT["portfolio_db"]

# 1. Seed Profile
COL_PROFILE = DB["profile"]
COL_PROFILE.delete_many({})
profile_data = {
    "full_name": "Ameer Hamza",
    "father_name": "Muhammad Zubair",
    "title": "AI & Data Science Developer",
    "tagline": "Building intelligent solutions with Python, ML & AI",
    "bio": "I'm Ameer Hamza, an ambitious AI & Data Science student from Hyderabad, Sindh. I am currently enrolled at Saylani Mass IT Training (SMIT) in the Artificial Intelligence and Data Science track. I also completed an Advance Computer Information Technology (ACIT) course at the Government Vocational Institute, Hyderabad. I actively participate in national-level tech events including the Indus AI Week Hackathon 2026.",
    "email": "ameerhamza031946@gmail.com",
    "phone": "0319-4613960",
    "location": "Hyderabad, Sindh, Pakistan",
    "province": "Sindh",
    "city": "Hyderabad",
    "roll_no": "AI-457375",
    "bano_qabil_id": "1366690",
    "years_experience": 1,
    "projects_count": 7,
    "photo_url": "/uploads/profile/hamza_photo.jpeg"
}
COL_PROFILE.insert_one(profile_data)

# 2. Seed Skills
COL_SKILLS = DB["skills"]
COL_SKILLS.delete_many({})
skills = [
    {"name": "Python", "percentage": 85, "category": "Core", "order_index": 1, "created_at": datetime.utcnow()},
    {"name": "Machine Learning", "percentage": 78, "category": "Core", "order_index": 2, "created_at": datetime.utcnow()},
    {"name": "Data Analysis", "percentage": 80, "category": "Core", "order_index": 3, "created_at": datetime.utcnow()},
    {"name": "HTML / CSS", "percentage": 75, "category": "Core", "order_index": 4, "created_at": datetime.utcnow()},
    {"name": "Computer Vision", "percentage": 65, "category": "Core", "order_index": 5, "created_at": datetime.utcnow()},
    {"name": "AI Applications", "percentage": 72, "category": "Core", "order_index": 6, "created_at": datetime.utcnow()}
]
COL_SKILLS.insert_many(skills)

# 3. Seed Certifications
COL_CERTIFICATIONS = DB["certifications"]
COL_CERTIFICATIONS.delete_many({})
certs = [
    {
        "name": "Advance Computer Information Technology (ACIT)",
        "issuer": "Government Vocational Institute · Govt of Sindh",
        "date_info": "Aug 2024 – Jan 2025",
        "registration_number": "GVI/ACIT/319",
        "description": "Successfully completed ACIT course at Government Vocational Institute, Affandi Town, Hyderabad.",
        "certificate_url": "/uploads/certifications/acit.jpeg",
        "order_index": 1,
        "created_at": datetime.utcnow()
    },
    {
        "name": "AI Hackathon — Indus AI Week 2026",
        "issuer": "Tech Pakistan · Ministry of IT & Telecom",
        "date_info": "2026",
        "registration_number": "Indus AI Week",
        "description": "Certificate of active participation in the AI Hackathon during Indus AI Week 2026, organized by Tech Pakistan, Saylani, NIC, and Govt of Sindh.",
        "certificate_url": "/uploads/certifications/ai_hackathon.png",
        "order_index": 2,
        "created_at": datetime.utcnow()
    },
    {
        "name": "Coding Night-2026 (Hackathon)",
        "issuer": "Saylani Mass Training Programme",
        "date_info": "Duration: 08 Hours",
        "registration_number": "SMIT/2026/Hackathon/457375",
        "description": "Successfully participated in the Coding Night-2026 Hackathon under the Education Department of Saylani Welfare International Trust.",
        "certificate_url": "/uploads/certifications/smit_hackathon.png",
        "order_index": 3,
        "created_at": datetime.utcnow()
    }
]
COL_CERTIFICATIONS.insert_many(certs)

print("Database seeded successfully with Profile, Skills, and Certifications.")
