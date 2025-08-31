from dotenv import load_dotenv
load_dotenv()
from notifiers.twilio_notifier import send_whatsapp
ok = send_whatsapp("✅ Test WhatsApp depuis Supplier Monitor Bot.")
print("send_whatsapp returned:", ok)
