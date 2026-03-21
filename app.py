# ===================================================================================================
# ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗    ███████╗██████╗ ██╗████████╗██╗  ██╗
# ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ██╔════╝██╔══██╗██║╚══██╔══╝██║  ██║
# ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗    █████╗  ██║  ██║██║   ██║   ███████║
# ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ██╔══╝  ██║  ██║██║   ██║   ██╔══██║
# ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║    ███████╗██████╔╝██║   ██║   ██║  ██║
# ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚══════╝╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝
# ===================================================================================================
#
# PROPRIETARY AND HIGHLY RESTRICTED SOURCE CODE
# © 2026 Shashank Gowda NB. All Rights Reserved.
#
# WARNING: STRICTLY PROHIBITED ACTIONS
# 1. You may NOT copy, distribute, modify, or resell this software without explicit written permission.
# 2. You may NOT remove, alter, or obscure this copyright header under any circumstances.
# 3. Unauthorized use, reverse engineering, or stripping of the Firebase Master Control is a 
#    direct violation of the licensing terms and is subject to legal action.
#
# LICENSING & CONTACT:
# This project is solely architected and owned by Shashank Gowda NB. 
# To purchase a commercial license, request modifications, or acquire authorized use rights,
# you MUST contact the original creator:
# Email: shashankgowdanb166@gmail.com
#
# ===================================================================================================

import os
import sys
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
import requests
from flask import Flask, render_template, render_template_string, request, jsonify, send_from_directory, session, redirect, url_for
from groq import Groq
from AppOpener import open as open_app, close as close_app
import urllib.parse
import json

# --- SCREEN READING IMPORTS & CONFIG ---
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
app.secret_key = 'nexus_core_secure_key_12345'

# ================= MASTER CONTROL SYSTEM (KILL-SWITCH) =================
FIREBASE_MASTER_URL = "https://jarvis-like-default-rtdb.firebaseio.com/master_control.json"

def trigger_custom_lockdown(msg, url):
    """
    Spawns a sleek, borderless, un-closable GUI lock screen 
    and instantly kills the main AI backend.
    """
    # We write a temporary UI script so it doesn't crash the Flask server threads
    lockdown_code = f"""
import tkinter as tk
import os

root = tk.Tk()
root.attributes('-topmost', True) # Forces window on top of EVERYTHING
root.overrideredirect(True) # Removes close buttons and borders
root.geometry("850x450")
root.configure(bg="#020406")

# Center on screen
x = (root.winfo_screenwidth()/2) - (850/2)
y = (root.winfo_screenheight()/2) - (450/2)
root.geometry(f'+{{int(x)}}+{{int(y)}}')

tk.Label(root, text="⚠ SECURITY ALERT: SYSTEM DEACTIVATED ⚠", fg="#ff3333", bg="#020406", font=("Courier", 24, "bold")).pack(pady=40)
tk.Label(root, text="{msg}", fg="#00f3ff", bg="#020406", font=("Courier", 14), wraplength=750).pack(pady=10)
tk.Label(root, text="{url}", fg="#00f3ff", bg="#020406", font=("Courier", 12)).pack(pady=10)
tk.Label(root, text="LICENSED EXCLUSIVELY BY SHASHANK GOWDA NB", fg="#555555", bg="#020406", font=("Courier", 10)).pack(side="bottom", pady=20)

tk.Button(root, text="ACKNOWLEDGE TERMINATION", bg="#ff3333", fg="white", font=("Courier", 14, "bold"), command=lambda: os._exit(0), relief="flat", padx=20, pady=10).pack(pady=40)

root.mainloop()
"""
    try:
        with open("system_lock.py", "w", encoding="utf-8") as f:
            f.write(lockdown_code)
        # Launch the lock screen
        subprocess.Popen([sys.executable, "system_lock.py"])
    except: pass
    
    # Kill the main AI process instantly
    os._exit(1)

def initial_boot_check():
    """PRE-BOOT CHECK: Runs synchronously before Flask even starts."""
    print("Verifying License Authentication with Mainframe...")
    try:
        response = requests.get(FIREBASE_MASTER_URL, timeout=5)
        if response.status_code == 200 and response.json():
            data = response.json()
            if data.get("is_locked", False):
                message = data.get("message", "This version of Nexus AI has been deactivated by the creator.")
                url = data.get("url", "Contact: shashankgowdanb166@gmail.com")
                trigger_custom_lockdown(message, url)
    except Exception as e:
        print("Master Server unreachable. Proceeding in offline mode.")

def master_control_monitor():
    """BACKGROUND THREAD: Checks continuously while the app is running."""
    while True:
        try:
            response = requests.get(FIREBASE_MASTER_URL, timeout=5)
            if response.status_code == 200 and response.json():
                data = response.json()
                if data.get("is_locked", False):
                    message = data.get("message", "This version of Nexus AI has been deactivated by the creator.")
                    url = data.get("url", "Contact: shashankgowdanb166@gmail.com")
                    trigger_custom_lockdown(message, url)
        except Exception as e:
            pass
        time.sleep(10)

# ================= CONFIGURATION =================
GROQ_API_KEY = "your-api-key-here"  # Replace with your actual Groq API key
client = Groq(api_key=GROQ_API_KEY)
MODEL_ID = "llama-3.3-70b-versatile"

vision_process = None
CONTACTS = { "shashank": "shashankgowdanb166@gmail.com" }

engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak_async(text):
    def _speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except: pass
    threading.Thread(target=_speak).start()

# ================= MEMORY SYSTEM CORE =================
MEMORY_FILE = 'nexus_memory.json'
DEFAULT_EXPIRY_DAYS = 30

def load_memory():
    if not os.path.exists(MEMORY_FILE): return {}
    try:
        with open(MEMORY_FILE, 'r') as f: mem = json.load(f)
        now = time.time()
        cleaned_mem = {}
        changed = False
        for k, v in mem.items():
            if 'expires_at' in v and v['expires_at'] < now: changed = True  
            else: cleaned_mem[k] = v
        if changed:
            with open(MEMORY_FILE, 'w') as f: json.dump(cleaned_mem, f, indent=4)
        return cleaned_mem
    except: return {}

def save_memory(key, value, days=DEFAULT_EXPIRY_DAYS):
    mem = load_memory()
    expires_at = time.time() + (float(days) * 86400)
    mem[key] = {"value": value, "expires_at": expires_at, "days": days}
    with open(MEMORY_FILE, 'w') as f: json.dump(mem, f, indent=4)

def delete_memory(key):
    mem = load_memory()
    if key in mem:
        del mem[key]
        with open(MEMORY_FILE, 'w') as f: json.dump(mem, f, indent=4)
        return True
    return False

def get_memory_context_string():
    mem = load_memory()
    if not mem: return "No specific user data stored yet."
    return "\n".join([f"- {k}: {v['value']}" for k, v in mem.items()])

# ================= SYSTEM PROMPT =================
SYSTEM_PROMPT = """
You are EDITH (Nexus AI), a highly advanced AI assistant.
When answering conversational questions, be concise (1-2 sentences maximum).

CRITICAL RULES:
1. NEVER invent your own commands. 
2. For general conversation, JUST ANSWER NORMALLY in plain text. DO NOT output any CMD.
3. ONLY output `CMD:WRITE:topic` if the user explicitly uses the exact word "write" or "type".
4. You have a permanent Memory System. If the user tells you personal details ABOUT THEMSELVES (like their name, likes, or facts about their life), you MUST save it using `CMD:MEMORY:SAVE:key:value`. 
   - ALWAYS write your natural conversational response FIRST, then put the CMD on a new line at the very end.
5. If the user asks you to forget something, use `CMD:MEMORY:DELETE:key`.

COMMANDS:
- Vision/Camera: `CMD:VISION:ON` | `CMD:VISION:OFF` | `CMD:SCREENSHOT` 
- Email: `CMD:EMAIL:recipient_name:topic`
- WhatsApp: `CMD:WHATSAPP:recipient_name:message_content`
- Apps: `CMD:OPEN:appname` | `CMD:CLOSE:appname`
- Web: `CMD:CLOSE_TAB`
- Volume: `CMD:VOL:UP:amount` | `CMD:VOL:DOWN:amount`
- Files: `CMD:FILE:OPEN:filename`
- Write Essay: `CMD:WRITE:topic`
- Presentation: `CMD:PPT:topic`
- Time/Date: `CMD:TIME_CHECK`
- Memory Save: `CMD:MEMORY:SAVE:key:value`
- Memory Delete: `CMD:MEMORY:DELETE:key`
"""

conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

# ================= HELPER FUNCTIONS =================
def get_active_window_context():
    import ctypes
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        window_title = buf.value.lower()
        if not window_title: return "You are viewing the desktop."
        if any(app in window_title for app in ["chrome", "edge", "firefox", "brave", "opera"]): return "You are browsing the internet."
        elif any(app in window_title for app in ["visual studio", "vscode", "pycharm", "sublime", "intellij"]): return "You are coding."
        elif any(app in window_title for app in ["notepad", "word", "docs"]): return "You are writing."
        elif "explorer" in window_title or "folder" in window_title: return "You are managing files."
        else: return f"You are currently focusing on: {buf.value}"
    except: return "I couldn't detect your current active window."

def scan_screen_for_text():
    if not os.path.exists(pytesseract.pytesseract.tesseract_cmd): return "ERROR: Tesseract OCR is not installed."
    try:
        screenshot = pyautogui.screenshot()
        extracted_text = pytesseract.image_to_string(screenshot).strip()
        if not extracted_text: return "ERROR: No readable text was found on the screen."
        return extracted_text[:1500] 
    except Exception as e: return f"ERROR: {str(e)}"

def get_current_time_date():
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A')}, {now.strftime('%d %B %Y')}. The current time is {now.strftime('%I:%M %p')}."

def find_file(filename_query):
    search_dirs = [os.path.join(os.path.expanduser("~"), "Desktop"), os.path.join(os.path.expanduser("~"), "Documents"), os.path.join(os.path.expanduser("~"), "Downloads")]
    clean_query = filename_query.lower().replace(" file", "").replace(" pdf", "").strip()
    best_match_path, highest_score = None, 0.0
    for d in search_dirs:
        if os.path.exists(d):
            for r, _, f in os.walk(d):
                for file in f:
                    file_lower = file.lower()
                    score = difflib.SequenceMatcher(None, clean_query, file_lower).ratio()
                    if clean_query in file_lower: score += 0.5
                    if score > highest_score and score > 0.4:
                        highest_score = score
                        best_match_path = os.path.join(r, file)
    return best_match_path

def generate_essay_content(topic):
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "system", "content": "You are a professional academic writer. Write a detailed, factually accurate essay."}, {"role": "user", "content": f"Write an essay on: {topic}"}],
            max_tokens=600
        )
        return completion.choices[0].message.content
    except: return "Error generating text."
    
def automated_email(contact_name, topic):
    email_addr = CONTACTS.get(contact_name.lower())
    if not email_addr: return f"I couldn't find {contact_name} in your contacts."
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "system", "content": "You are writing an email. Keep it short and professional."}, {"role": "user", "content": f"Write an email to {contact_name} about {topic}"}],
            max_tokens=200
        )
        email_body = completion.choices[0].message.content
    except: email_body = f"Hello, I am writing to you regarding {topic}."

    params = {"view": "cm", "fs": "1", "to": email_addr, "su": f"Regarding {topic}", "body": email_body}
    webbrowser.open(f"https://mail.google.com/mail/?{urllib.parse.urlencode(params)}")
    time.sleep(8); pyautogui.hotkey('ctrl', 'enter'); time.sleep(2); pyautogui.hotkey('ctrl', 'w')
    return f"Email sent to {contact_name}."

# ================= COMMAND LOGIC =================
def execute_command(cmd_str):
    global vision_process
    print(f"Executing: {cmd_str}") 
    try:
        raw_parts = cmd_str.split(":", 4)
        parts = [raw_parts[i] if i < len(raw_parts) else "" for i in range(5)]
        action = parts[1]
        
        if action == "VISION":
            sub_cmd = parts[2]
            if sub_cmd == "FACE":
                pyautogui.hotkey('ctrl', 'w'); time.sleep(0.5)
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

        elif action == "MEMORY":
            if parts[2] == "SAVE" and parts[3] and parts[4]: save_memory(parts[3].strip(), parts[4].strip()); return None 
            elif parts[2] == "DELETE": delete_memory(parts[3].strip()); return None 

        elif action == "TIME_CHECK":
            time_info = get_current_time_date()
            speak_async(time_info)
            return time_info

        elif action == "WRITE_PDF":
            path = find_file(parts[2])
            if not path: return f"I couldn't find a file named '{parts[2]}'."
            summary = pdf_bot.get_pdf_summary(parts[2], path, client, MODEL_ID)
            open_app("notepad", match_closest=True); time.sleep(2); pyautogui.hotkey('ctrl', 'n'); time.sleep(1)
            pyautogui.write(f"SUMMARY OF: {parts[2]}\n\n", interval=0.01)
            pyautogui.write(summary, interval=0.005)
            return f"Summary written to Notepad."

        elif action == "PPT": return ppt_generator.generate_ppt(parts[2], client, MODEL_ID)
            
        elif action == "WHATSAPP":
            msg = parts[3] if parts[3] else "Hello"
            res = whatsapp_bot.send_whatsapp_message(parts[2], msg)
            if res == "MISSING_CONTACT":
                webbrowser.open("http://127.0.0.1:5000/whatsapp_manager")
                return f"Contact '{parts[2]}' not found. Opening WhatsApp Manager."
            return res

        elif action == "OPEN":
            try: open_app(parts[2], match_closest=True, throw_error=True); return f"Opening {parts[2]}."
            except: return f"Could not find {parts[2]}."
            
        elif action == "CLOSE":
            try: close_app(parts[2], match_closest=True, throw_error=True); return f"Closing {parts[2]}."
            except: return f"Could not close {parts[2]}."
            
        elif action == "CLOSE_TAB": pyautogui.hotkey('ctrl', 'w'); return "Tab closed."
            
        elif action == "VOL":
            try: amount = int(''.join(filter(str.isdigit, parts[3]))) if parts[3] else 10
            except: amount = 10
            if parts[2] == "UP": pyautogui.press('volumeup', presses=int(amount/2))
            else: pyautogui.press('volumedown', presses=int(amount/2))
            return f"Volume adjusted."
            
        elif action == "WRITE":
            open_app("notepad", match_closest=True); time.sleep(2); pyautogui.hotkey('ctrl', 'n'); time.sleep(1)
            pyautogui.write(generate_essay_content(parts[2]), interval=0.001)
            return f"Essay written."
            
        elif action == "EMAIL": return automated_email(parts[2], parts[3] if parts[3] else "General Inquiry")
            
        elif action == "SCREENSHOT":
            try:
                folder = os.path.join(os.path.join(os.path.expanduser("~"), "Desktop"), "Jarvis_Screenshots")
                if not os.path.exists(folder): os.makedirs(folder)
                pyautogui.screenshot().save(os.path.join(folder, f"screenshot_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"))
                return f"Screenshot saved."
            except: return "Failed to take screenshot."
            
        elif action == "FILE":
            path = find_file(parts[2]) 
            if path: os.startfile(path); return f"Opening {parts[2]}."
            else: return "File not found."
            
        return None
    except Exception as e:
        print(f"Error in execute_command: {e}")
        return "Command execution failed."

# ================= ROUTES =================
@app.route('/login')
def login_page(): return render_template('index.html')

@app.route('/')
def main_menu(): return render_template('index.html')

@app.route('/context_ui')
def context_ui():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Context Scanner</title>
        <style>
            body { font-family: 'Courier New', monospace; background: #020406; color: #00f3ff; padding: 30px; text-align: center; }
            button { background: rgba(0, 243, 255, 0.1); border: 1px solid #00f3ff; color: #00f3ff; padding: 15px 30px; font-size: 1.2rem; cursor: pointer; transition: 0.3s; }
            button:hover { background: #00f3ff; color: #000; box-shadow: 0 0 15px #00f3ff; }
            #context-result { margin-top: 30px; font-size: 1.5rem; background: rgba(0, 243, 255, 0.05); border: 1px dashed #00f3ff; padding: 20px; }
        </style>
    </head>
    <body>
        <h2>ACTIVE WINDOW CONTEXT</h2>
        <button onclick="checkContext()">SCAN CURRENT ACTIVITY</button>
        <div id="context-result">Awaiting scan...</div>
        <script>
            async function checkContext() {
                document.getElementById('context-result').innerText = "Scanning...";
                const res = await fetch('/api/context');
                const data = await res.json();
                document.getElementById('context-result').innerText = data.context;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/context', methods=['GET'])
def api_context(): return jsonify({"context": get_active_window_context()})

@app.route('/memory_manager')
def memory_manager():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Memory Core</title>
        <style>
            body { font-family: 'Courier New', monospace; background: #020406; color: #00f3ff; padding: 30px; }
            h2 { border-bottom: 1px solid #00f3ff; padding-bottom: 10px; }
            .control-panel { margin-bottom: 20px; display: flex; gap: 10px; }
            input, button { background: rgba(0, 243, 255, 0.1); border: 1px solid #00f3ff; color: #00f3ff; padding: 10px; outline: none; }
            button { cursor: pointer; transition: 0.3s; font-weight: bold; }
            button:hover { background: #00f3ff; color: #000; }
            .mem-item { background: rgba(0, 243, 255, 0.05); border-left: 3px solid #00f3ff; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
            .del-btn { background: rgba(255, 51, 51, 0.1); border: 1px solid #ff3333; color: #ff3333; }
            .del-btn:hover { background: #ff3333; color: #fff; }
        </style>
    </head>
    <body>
        <h2>NEURAL MEMORY CORE (Manual Control)</h2>
        <div class="control-panel">
            <input type="text" id="memKey" placeholder="Memory Key">
            <input type="text" id="memVal" placeholder="Value" style="flex-grow: 1;">
            <input type="number" id="memDays" value="30" style="width: 70px;">
            <button onclick="saveMemory()">INJECT MEMORY</button>
        </div>
        <div id="memoryList"></div>
        <script>
            async function loadMemory() {
                const res = await fetch('/api/memory'); const data = await res.json();
                const list = document.getElementById('memoryList'); list.innerHTML = "";
                if(Object.keys(data).length === 0) { list.innerHTML = "<p>Memory banks empty.</p>"; return; }
                for(let key in data) {
                    let div = document.createElement('div'); div.className = 'mem-item';
                    div.innerHTML = `<div><strong>${key.toUpperCase()}</strong> : ${data[key].value} <br><small style="opacity:0.6">Expires in: ${data[key].days} days</small></div>
                                     <button class="del-btn" onclick="deleteMemory('${key}')">PURGE</button>`;
                    list.appendChild(div);
                }
            }
            async function saveMemory() {
                const key = document.getElementById('memKey').value, val = document.getElementById('memVal').value, days = document.getElementById('memDays').value;
                if(!key || !val) return;
                await fetch('/api/memory', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: key, value: val, days: days}) });
                document.getElementById('memKey').value = ""; document.getElementById('memVal').value = ""; loadMemory();
            }
            async function deleteMemory(key) { await fetch(`/api/memory?key=${encodeURIComponent(key)}`, {method: 'DELETE'}); loadMemory(); }
            loadMemory();
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/memory', methods=['GET', 'POST', 'DELETE'])
def api_memory():
    if request.method == 'GET': return jsonify(load_memory())
    elif request.method == 'POST': save_memory(request.json.get('key'), request.json.get('value'), request.json.get('days', DEFAULT_EXPIRY_DAYS)); return jsonify({"status": "saved"})
    elif request.method == 'DELETE': delete_memory(request.args.get('key')); return jsonify({"status": "deleted"})

@app.route('/set-session', methods=['POST'])
def set_session():
    try: session['logged_in'] = True; session.permanent = True; return jsonify({"status": "success"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/jarvis')
def jarvis_ui(): return render_template('index.html')

@app.route('/nova')
def nova_ui(): return send_from_directory('.', 'nova.html')

@app.route('/sign_scanner')
def sign_scanner(): return render_template('sign_scanner.html')

@app.route('/whatsapp_manager')
def whatsapp_manager_ui(): return render_template('whatsapp_manager.html')

@app.route('/add_whatsapp_contact', methods=['POST'])
def add_whatsapp_contact(): return jsonify({"message": whatsapp_bot.save_contact_to_db(request.json['name'], request.json['phone'])})

@app.route('/get_whatsapp_contacts')
def get_whatsapp_contacts(): return jsonify(whatsapp_bot.load_contacts())

@app.route('/<path:filename>')
def serve_static(filename):
    try:
        if os.path.exists(os.path.join('.', filename)): return send_from_directory('.', filename)
        elif os.path.exists(os.path.join('templates', filename)): return send_from_directory('templates', filename)
        else: return jsonify({"error": "File not found"}), 404
    except Exception as e: return jsonify({"error": str(e)}), 500

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
    lower = user_text.lower()
    
    if any(x in lower for x in ["who created you", "who made you", "who is your creator", "who built you"]):
        reply = "I am the Nexus AI system, originally engineered and built by Shashank Gowda NB."
        conversation_history.append({"role": "user", "content": user_text})
        conversation_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})
        
    conversation_history.append({"role": "user", "content": user_text})
    if len(conversation_history) > 8: conversation_history.pop(1)

    try:
        current_memory = get_memory_context_string()
        dynamic_system_prompt = SYSTEM_PROMPT + f"\n\nCURRENT USER STORED MEMORY:\n{current_memory}"
        payload_history = [{"role": "system", "content": dynamic_system_prompt}] + conversation_history[1:]

        completion = client.chat.completions.create(model=MODEL_ID, messages=payload_history, temperature=0.6, max_tokens=150)
        ai_response = completion.choices[0].message.content.strip()
        reply_text = ""
        
        if "CMD:" in ai_response:
            cmd_start = ai_response.find("CMD:")
            command = ai_response[cmd_start:].split("\n")[0].strip()
            conv_part = ai_response[:cmd_start].strip()

            if "CMD:WRITE:" in command and not any(word in lower for word in ["write", "type", "essay", "report"]):
                reply_text = conv_part if conv_part else "I am here to assist."
                
            elif "CMD:VISION:READ" in command:
                raw_text = scan_screen_for_text()
                if raw_text.startswith("ERROR:"): reply_text = raw_text.replace("ERROR:", "Optical sensor failure:")
                else:
                    temp_history = payload_history.copy()
                    temp_history.append({"role": "user", "content": f"User asked what's on screen. Raw text: [{raw_text}]. Summarize naturally in 1-2 sentences."})
                    reply_text = client.chat.completions.create(model=MODEL_ID, messages=temp_history, temperature=0.5, max_tokens=150).choices[0].message.content.strip()
                    
            elif "CMD:CONTEXT" in command:
                context_data = get_active_window_context()
                temp_history = payload_history.copy()
                temp_history.append({"role": "user", "content": f"User asked what they are doing. Detected active window: [{context_data}]. Answer naturally."})
                reply_text = client.chat.completions.create(model=MODEL_ID, messages=temp_history, temperature=0.5, max_tokens=150).choices[0].message.content.strip()
                
            else:
                cmd_result = execute_command(command)
                if cmd_result: reply_text = cmd_result
                else:
                    reply_text = conv_part
                    if not reply_text: reply_text = "System command executed."
        else:
            reply_text = ai_response
        
        conversation_history.append({"role": "assistant", "content": reply_text})
        return jsonify({"reply": reply_text})

    except Exception as e:
        return jsonify({"reply": f"System error: {str(e)}"})

def open_browser(): 
    webbrowser.open_new("http://127.0.0.1:5000/")
    
if __name__ == '__main__':
    # 1. PRE-BOOT CHECK
    initial_boot_check()
    
    # 2. START BACKGROUND MONITOR
    control_thread = threading.Thread(target=master_control_monitor, daemon=True)
    control_thread.start()
    
    if not os.path.exists('templates'): os.makedirs('templates')
    threading.Timer(1.5, open_browser).start()
    
    print("\n" + "="*50)
    print("NEXUS CORE ACTIVE | LICENSED BY: SHASHANK GOWDA NB")
    print("="*50 + "\n")
    
    app.run(port=5000, debug=False)
