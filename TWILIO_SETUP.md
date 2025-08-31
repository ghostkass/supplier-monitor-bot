# Guide Twilio/WhatsApp

1) Ouvre ton console Twilio > Messaging > Try it out > WhatsApp Sandbox.
2) Envoie depuis ton téléphone le message **join <ton_code>** au numéro sandbox (souvent +1 415 523 8886).
3) Mets ces variables dans `.env` :
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ALERT_TO_WHATSAPP=whatsapp:+XXXXXXXXXXX
4) Installe le SDK: `pip install twilio==9.0.0`
5) Test: `python test_whatsapp.py`
6) Le bot enverra désormais en **email** et en **WhatsApp** (si configurés).

En prod (numéro Business), remplace le FROM par ton numéro WhatsApp approuvé.
