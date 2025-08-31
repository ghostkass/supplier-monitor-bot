import os
from dotenv import load_dotenv
load_dotenv()

try:
    from twilio.rest import Client
except Exception as e:
    Client = None

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")  # e.g., 'whatsapp:+14155238886' (sandbox)
WHATSAPP_TO = os.getenv("ALERT_TO_WHATSAPP") or os.getenv("TWILIO_WHATSAPP_TO")

def send_whatsapp(body: str, to: str = None):
    to_num = to or WHATSAPP_TO
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, WHATSAPP_FROM, to_num]) or Client is None:
        print(f"[ALERT][WA-DRY-RUN] {body}\n(raison: Twilio non configuré)")
        return False
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(from_=WHATSAPP_FROM, to=to_num, body=body)
        print(f"[ALERT][WA-SENT] -> {to_num} | sid={msg.sid}")
        return True
    except Exception as e:
        print(f"[ALERT][WA-ERROR] {e}")
        return False
