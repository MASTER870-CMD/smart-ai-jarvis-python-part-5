import pywhatkit
import json
import os
import pyautogui
import time

# File to store contacts
DB_FILE = "contacts.json"

def load_contacts():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_contact_to_db(name, phone):
    contacts = load_contacts()
    # Ensure phone has country code (default to +91 if missing)
    if not phone.startswith("+"):
        phone = "+91" + phone
    contacts[name.lower()] = phone
    
    with open(DB_FILE, 'w') as f:
        json.dump(contacts, f, indent=4)
    return f"Saved {name} with number {phone}"

def send_whatsapp_message(name, message):
    contacts = load_contacts()
    phone = contacts.get(name.lower())

    if not phone:
        # RETURN SPECIAL SIGNAL IF NOT FOUND
        return "MISSING_CONTACT"

    try:
        # 1. Send the message
        pywhatkit.sendwhatmsg_instantly(
            phone_no=phone, 
            message=message, 
            wait_time=20, 
            tab_close=True, 
            close_time=3
        )
        
        # Force a backup close command just in case
        time.sleep(2) 
        pyautogui.press('enter') 
        
        return f"Message sent to {name}."
    except Exception as e:
        return f"Failed to send WhatsApp message: {str(e)}"