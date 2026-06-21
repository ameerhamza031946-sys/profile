# Ameer Hamza - Portfolio Backend

This repository contains the backend code for my personal portfolio website. It is built using FastAPI and MongoDB.

## Features
- Complete REST API for managing profile details, skills, projects, and certifications.
- Contact form integration with email notifications (SMTP).
- Rate limiting to prevent abuse.
- MongoDB integration using `motor` for asynchronous operations.
- Admin authentication with JWT.

## Tech Stack
- **Framework:** FastAPI
- **Database:** MongoDB (via Motor)
- **Authentication:** JWT & bcrypt
- **Other Tools:** Pydantic, SlowAPI, python-multipart

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ameerhamza031946-sys/profile.git
   cd profile
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and configure the following:
   ```env
   MONGO_URL=mongodb+srv://<user>:<password>@cluster...
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASS=your_app_password
   OWNER_EMAIL=your_email@gmail.com
   SECRET_KEY=your_secure_random_string
   ALLOWED_ORIGIN=*
   ```

5. **Run the server:**
   ```bash
   uvicorn portfolio_backend:app --reload
   ```

## API Documentation
Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
