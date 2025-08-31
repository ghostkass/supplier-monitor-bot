import os, smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or "monitor@example.com")
ALERT_TO = os.getenv("ALERT_TO")

def send_email(subject: str, body: str, to: str = None):
    to_addr = to or ALERT_TO
    if not (SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD and to_addr):
        # Fallback: print only
        print("[ALERT][DRY-RUN]", subject, body)
        return False

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Supplier Monitor Bot", SMTP_FROM))
    msg["To"] = to_addr

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_addr], msg.as_string())
    return True
