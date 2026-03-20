
import os
import webbrowser
import pyautogui
import threading
import subprocess
import time
import datetime
import pyttsx3 
import ppt_generator
import whatsapp_bot 
import pdf_bot
import difflib
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from groq import Groq
from AppOpener import open as open_app, close as close_app
import urllib.parse
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this_in_production'

# ================= CONFIGURATION =================
GROQ_API_KEY = "your_groq_api_key_here"  # Replace with your actual Groq API key
client = Groq(api_key=GROQ_API_KEY)
MODEL_ID = "llama-3.3-70b-versatile"

vision_process = None

# Email contacts
CONTACTS = {
    "shashank": "shashankgowdanb166@gmail.com",
}

engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak_async(text):
    def _speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except: pass
    threading.Thread(target=_speak).start()

# ================= SYSTEM PROMPT =================
SYSTEM_PROMPT = """
You are EDITH (Nexus AI).
When answering normally, be extremely concise and accurate (1-2 complete sentences maximum).
Do not provide long explanations in chat. 

CRITICAL RULES:
- If the user asks for more information (e.g., "What is AI?", "Tell me more"), just answer them directly in chat. Do NOT use the WRITE command.
- ONLY output `CMD:WRITE:topic` if the user explicitly uses the exact word "write" or "type" (e.g., "Write an essay on...", "Type a report on...").

COMMANDS:
- Vision: `CMD:VISION:ON` | `CMD:VISION:OFF` `CMD:SCREENSHOT`
- Email: `CMD:EMAIL:recipient_name:topic`
- WhatsApp: `CMD:WHATSAPP:recipient_name:message_content`
- Apps: `CMD:OPEN:appname` | `CMD:CLOSE:appname`
- Web: `CMD:CLOSE_TAB`
- Volume: `CMD:VOL:UP:amount` | `CMD:VOL:DOWN:amount`
- Files: `CMD:FILE:OPEN:filename`
- Write Essay: `CMD:WRITE:topic` (STRICTLY ONLY IF USER SAYS 'WRITE')
- Presentation: `CMD:PPT:topic`
- Time/Date: `CMD:TIME_CHECK`
"""

conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

# ================= HELPER FUNCTIONS =================
def get_current_time_date():
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")
    return f"Today is {day_name}, {date_str}. The current time is {time_str}."

def find_file(filename_query):
    search_dirs = [os.path.join(os.path.expanduser("~"), "Desktop"), 
                   os.path.join(os.path.expanduser("~"), "Documents"),
                   os.path.join(os.path.expanduser("~"), "Downloads")]
    
    clean_query = filename_query.lower().replace(" file", "").replace(" pdf", "").strip()
    best_match_path = None
    highest_score = 0.0

    for d in search_dirs:
        if os.path.exists(d):
            for r, _, f in os.walk(d):
                for file in f:
                    file_lower = file.lower()
                    score = difflib.SequenceMatcher(None, clean_query, file_lower).ratio()
                    if clean_query in file_lower:
                        score += 0.5
                    if score > highest_score and score > 0.4:
                        highest_score = score
                        best_match_path = os.path.join(r, file)
    return best_match_path

def generate_essay_content(topic):
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a professional academic writer. Write a detailed, factually accurate essay. STRICTLY NO SPELLING MISTAKES."},
                {"role": "user", "content": f"Write an essay on: {topic}"}
            ],
            max_tokens=600
        )
        return completion.choices[0].message.content
    except: return "Error generating text."
    
def automated_email(contact_name, topic):
    email_addr = CONTACTS.get(contact_name.lower())
    if not email_addr:
        return f"I couldn't find {contact_name} in your contacts."

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are writing an email. Keep it short, professional, and concise. No subject lines in body."},
                {"role": "user", "content": f"Write an email to {contact_name} about {topic}"}
            ],
            max_tokens=200
        )
        email_body = completion.choices[0].message.content
    except:
        email_body = f"Hello, I am writing to you regarding {topic}."

    params = {"view": "cm", "fs": "1", "to": email_addr, "su": f"Regarding {topic}", "body": email_body}
    query_string = urllib.parse.urlencode(params) 
    url = f"https://mail.google.com/mail/?{query_string}"

    webbrowser.open(url)
    time.sleep(8) 
    pyautogui.hotkey('ctrl', 'enter')
    time.sleep(2)
    pyautogui.hotkey('ctrl', 'w')
    
    return f"Email sent to {contact_name}."

# ================= COMMAND LOGIC =================
def execute_command(cmd_str):
    global vision_process
    print(f"Executing: {cmd_str}") 
    try:
        # FIX 1: Safely split and pad to prevent IndexError crashes
        raw_parts = cmd_str.split(":")
        parts = [raw_parts[i] if i < len(raw_parts) else "" for i in range(4)]
        
        action = parts[1]
        
        if action == "VISION":
            sub_cmd = parts[2]
            if sub_cmd == "FACE":
                pyautogui.hotkey('ctrl', 'w')
                time.sleep(0.5)
                if vision_process is None or vision_process.poll() is not None:
                    vision_process = subprocess.Popen(["python", "face_system.py"])
                    return "Initializing Human Detection Protocols."
                return "Face scanner is already active."
            elif sub_cmd == "SIGN":
                if vision_process: vision_process.terminate(); vision_process = None
                webbrowser.open("http://127.0.0.1:5000/sign_scanner")
                return "Initializing Sign Language Decoder."
            elif sub_cmd == "OFF":
                if vision_process: vision_process.terminate(); vision_process = None
                pyautogui.hotkey('ctrl', 'w')
                return "Vision systems deactivated."

        elif action == "TIME_CHECK":
            time_info = get_current_time_date()
            speak_async(time_info)
            return time_info

        elif action == "WRITE_PDF":
            filename_query = parts[2]
            path = find_file(filename_query)
            if not path:
                return f"I couldn't find a file named '{filename_query}'."
            
            summary = pdf_bot.get_pdf_summary(filename_query, path, client, MODEL_ID)
            open_app("notepad", match_closest=True)
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(1)
            pyautogui.write(f"SUMMARY OF: {filename_query}\n\n", interval=0.01)
            pyautogui.write(summary, interval=0.005)
            return f"Summary written to Notepad."

        elif action == "PPT":
            topic = parts[2]
            return ppt_generator.generate_ppt(topic, client, MODEL_ID)
            
        elif action == "WHATSAPP":
            recipient = parts[2]
            message = parts[3]
            if not message: message = "Hello" # Fallback if AI forgets message
            result = whatsapp_bot.send_whatsapp_message(recipient, message)
            if result == "MISSING_CONTACT":
                webbrowser.open("http://127.0.0.1:5000/whatsapp_manager")
                return f"Contact '{recipient}' not found. Opening WhatsApp Manager."
            return result

        elif action == "OPEN":
            try: open_app(parts[2], match_closest=True, throw_error=True); return f"Opening {parts[2]}.";
            except: return f"Could not find {parts[2]}."
            
        elif action == "CLOSE":
            try: close_app(parts[2], match_closest=True, throw_error=True); return f"Closing {parts[2]}.";
            except: return f"Could not close {parts[2]}."
            
        elif action == "CLOSE_TAB":
            pyautogui.hotkey('ctrl', 'w')
            return "Tab closed."
            
        elif action == "VOL":
            direction = parts[2]
            try: amount = int(''.join(filter(str.isdigit, parts[3]))) if parts[3] else 10
            except: amount = 10
            presses = int(amount / 2)
            if direction == "UP": pyautogui.press('volumeup', presses=presses)
            else: pyautogui.press('volumedown', presses=presses)
            return f"Volume adjusted."
            
        elif action == "WRITE":
            topic = parts[2]
            open_app("notepad", match_closest=True)
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(1)
            content = generate_essay_content(topic)
            pyautogui.write(content, interval=0.001)
            return f"Essay written."
            
        elif action == "EMAIL":
            recipient = parts[2]
            topic = parts[3] if parts[3] else "General Inquiry"
            return automated_email(recipient, topic)
            
        elif action == "SCREENSHOT":
            try:
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                folder_path = os.path.join(desktop_path, "Jarvis_Screenshots")
                if not os.path.exists(folder_path): os.makedirs(folder_path)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"screenshot_{timestamp}.png"
                save_path = os.path.join(folder_path, filename)
                pyautogui.screenshot().save(save_path)
                return f"Screenshot saved."
            except: return "Failed to take screenshot."
            
        elif action == "FILE":
            path = find_file(parts[2]) # FIX 2: Switched parts[3] to parts[2] for filename
            if path: os.startfile(path); return f"Opening {parts[2]}."
            else: return "File not found."

    except Exception as e:
        print(f"Error in execute_command: {e}")
        return "Command failed."
    return "Done."

# ================= ROUTES =================
@app.route('/login')
def login_page():
    return render_template('index.html')

@app.route('/')
def main_menu():
    return render_template('index.html')

@app.route('/set-session', methods=['POST'])
def set_session():
    try:
        session['logged_in'] = True
        session.permanent = True 
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Session error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/jarvis')
def jarvis_ui():
    return render_template('index.html')

@app.route('/nova')
def nova_ui():
    return send_from_directory('.', 'nova.html')

@app.route('/sign_scanner')
def sign_scanner(): 
    return render_template('sign_scanner.html')

@app.route('/whatsapp_manager')
def whatsapp_manager_ui():
    return render_template('whatsapp_manager.html')

@app.route('/add_whatsapp_contact', methods=['POST'])
def add_whatsapp_contact():
    data = request.json
    msg = whatsapp_bot.save_contact_to_db(data['name'], data['phone'])
    return jsonify({"message": msg})

@app.route('/get_whatsapp_contacts')
def get_whatsapp_contacts():
    return jsonify(whatsapp_bot.load_contacts())

@app.route('/<path:filename>')
def serve_static(filename):
    try:
        if os.path.exists(os.path.join('.', filename)):
            return send_from_directory('.', filename)
        elif os.path.exists(os.path.join('templates', filename)):
            return send_from_directory('templates', filename)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/start_jarvis_backend', methods=['POST'])
def start_jarvis_backend():
    global vision_process
    if vision_process is None or vision_process.poll() is not None:
        vision_process = subprocess.Popen(["python", "face_system.py"])
        speak_async("Edith visual systems online.")
        return jsonify({"status": "started"})
    return jsonify({"status": "already_running"})

@app.route('/process', methods=['POST'])
def process():
    user_text = request.json.get('text', '')
    conversation_history.append({"role": "user", "content": user_text})
    if len(conversation_history) > 8: conversation_history.pop(1)

    try:
        reply_text = ""
        cmd_trigger = None
        lower = user_text.lower()
        
        # 1. Vision Triggers
        if any(x in lower for x in ["scan for humans", "detect face", "open camera"]):
            cmd_trigger = "CMD:VISION:FACE"
        elif any(x in lower for x in ["scan for signs", "sign language"]):
            cmd_trigger = "CMD:VISION:SIGN"
        elif any(x in lower for x in ["stop scanning", "vision off", "close camera"]):
            cmd_trigger = "CMD:VISION:OFF"
            
        # 2. PPT Trigger
        elif "presentation" in lower or "ppt" in lower:
             topic = lower.replace("create", "").replace("presentation", "").replace("ppt", "").replace("about", "").replace("on", "").strip()
             cmd_trigger = f"CMD:PPT:{topic}"

        # 3. WhatsApp Trigger - FIX 3: More reliable parsing
        elif "message" in lower or "whatsapp" in lower:
             if "to" in lower:
                 try:
                     after_to = lower.split(" to ", 1)[1]
                     if " saying " in after_to:
                         recipient, msg_content = after_to.split(" saying ", 1)
                         cmd_trigger = f"CMD:WHATSAPP:{recipient.strip()}:{msg_content.strip()}"
                 except: pass
        
        # 4. WRITE PDF Trigger
        elif "write" in lower and "summary" in lower and "pdf" in lower:
            filename = lower.replace("write", "").replace("summary", "").replace("of", "").replace("pdf", "").replace("in", "").replace("notepad", "").strip()
            cmd_trigger = f"CMD:WRITE_PDF:{filename}"
            
        # 5. Time/Date Trigger
        elif any(x in lower for x in ["time", "date", "day is it", "today"]):
            cmd_trigger = "CMD:TIME_CHECK"

        if cmd_trigger:
            reply_text = execute_command(cmd_trigger)

        # 6. AI Trigger
        else:
            completion = client.chat.completions.create(
                model=MODEL_ID, messages=conversation_history, temperature=0.6, max_tokens=150
            )
            ai_response = completion.choices[0].message.content.strip()
            
            if "CMD:" in ai_response:
                cmd_start = ai_response.find("CMD:")
                command = ai_response[cmd_start:].split("\n")[0]
                
                # SAFETY CHECK
                if "CMD:WRITE:" in command and not any(word in lower for word in ["write", "type", "essay"]):
                    print("Blocked unwanted Notepad write. Forcing normal chat response.")
                    temp_history = conversation_history.copy()
                    temp_history.append({"role": "system", "content": "Just answer the question conversationally. DO NOT use CMD:WRITE."})
                    fallback_comp = client.chat.completions.create(model=MODEL_ID, messages=temp_history, max_tokens=150)
                    reply_text = fallback_comp.choices[0].message.content.strip()
                else:
                    reply_text = execute_command(command)
            else:
                reply_text = ai_response
        
        conversation_history.append({"role": "assistant", "content": reply_text})
        return jsonify({"reply": reply_text})

    except Exception as e:
        return jsonify({"reply": f"System error: {str(e)}"})

def open_browser(): 
    webbrowser.open_new("http://127.0.0.1:5000/")
    
if __name__ == '__main__':
    if not os.path.exists('templates'): os.makedirs('templates')
    threading.Timer(1.5, open_browser).start()
    print("EDITH MAIN SYSTEM ONLINE...")
    app.run(port=5000, debug=False)