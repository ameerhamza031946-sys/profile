import pymongo
from datetime import datetime

MONGO_URL = "mongodb://localhost:27017"
CLIENT = pymongo.MongoClient(MONGO_URL)
DB = CLIENT["portfolio_db"]
COL_PROJECTS = DB["projects"]

projects = [
    {
        "title": "AI Chatbot",
        "description": "An intelligent conversational agent built with modern AI technologies.",
        "tech_stack": "React, AI",
        "live_url": "https://chatbot-gamma-rose-68.vercel.app/",
        "category": "AI / ML",
        "is_featured": True,
        "order_index": 1,
        "created_at": datetime.utcnow()
    },
    {
        "title": "Dashboard Frontend",
        "description": "A sleek and responsive analytics dashboard interface.",
        "tech_stack": "React, Frontend",
        "live_url": "https://dashfront-sepia.vercel.app/",
        "category": "Web Development",
        "is_featured": True,
        "order_index": 2,
        "created_at": datetime.utcnow()
    },
    {
        "title": "Coffee Shop Website",
        "description": "A visually appealing frontend interface for a coffee shop.",
        "tech_stack": "React, Frontend",
        "live_url": "https://cofefront.vercel.app/",
        "category": "Web Development",
        "is_featured": True,
        "order_index": 3,
        "created_at": datetime.utcnow()
    },
    {
        "title": "Gym Management Portal",
        "description": "A comprehensive web interface for gym management and member login.",
        "tech_stack": "React, Frontend",
        "live_url": "https://frontendgym-ten.vercel.app/login",
        "category": "Web Development",
        "is_featured": True,
        "order_index": 4,
        "created_at": datetime.utcnow()
    },
    {
        "title": "Mind Guard AI",
        "description": "An AI-powered application focused on mental wellness and guarding.",
        "tech_stack": "React, AI",
        "live_url": "https://mind-guard-ai-ten.vercel.app/",
        "category": "AI / ML",
        "is_featured": True,
        "order_index": 5,
        "created_at": datetime.utcnow()
    },
    {
        "title": "E-Commerce Platform",
        "description": "A modern and fully responsive e-commerce web application.",
        "tech_stack": "React, Frontend",
        "live_url": "https://e-commerce-one-chi-20.vercel.app/",
        "category": "Web Development",
        "is_featured": True,
        "order_index": 6,
        "created_at": datetime.utcnow()
    },
    {
        "title": "Multi-Modal AI App",
        "description": "An intelligent multi-modal AI application built using Streamlit.",
        "tech_stack": "Streamlit, AI",
        "live_url": "https://maltimodel-ujg4mngdz955xuynmramrm.streamlit.app/",
        "category": "AI / ML",
        "is_featured": True,
        "order_index": 7,
        "created_at": datetime.utcnow()
    }
]

# Clear existing projects
COL_PROJECTS.delete_many({})

# Insert new ones
COL_PROJECTS.insert_many(projects)
print("Projects inserted successfully.")
