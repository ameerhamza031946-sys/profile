import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")

print(f"Testing SMTP with config:")
print(f"Host: {SMTP_HOST}:{SMTP_PORT}")
print(f"User: {SMTP_USER}")
print(f"Pass length: {len(SMTP_PASS)}")
print(f"To: {OWNER_EMAIL}")

if not SMTP_USER or not SMTP_PASS:
    print("ERROR: SMTP_USER or SMTP_PASS is missing in .env!")
    exit(1)

# Clean password spaces just in case
clean_pass = SMTP_PASS.replace(" ", "")
print(f"Cleaned Pass length: {len(clean_pass)}")

try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Test SMTP Connection"
    msg["From"] = SMTP_USER
    msg["To"] = OWNER_EMAIL
    msg.attach(MIMEText("This is a test email to verify SMTP credentials.", "plain"))

    print("Connecting to SMTP server...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        print("Starting TLS...")
        server.starttls()
        print("Logging in...")
        server.login(SMTP_USER, clean_pass)
        print("Sending mail...")
        server.sendmail(SMTP_USER, OWNER_EMAIL, msg.as_string())
    print("SUCCESS: Email sent successfully!")
except Exception as e:
    print(f"FAILED: SMTP test failed with error: {e}")
