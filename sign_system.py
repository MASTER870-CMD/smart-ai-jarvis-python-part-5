import cv2
import time
import threading
import speech_recognition as sr
import pyttsx3
import numpy as np

# --- CONFIGURATION ---
running = True
last_spoken_time = 0

# --- VOICE OUTPUT ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak_async(text):
    """Speaks without freezing the video"""
    def _speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except: pass
    threading.Thread(target=_speak).start()

# --- VOICE INPUT (THREADED) ---
def listen_for_stop():
    global running
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    while running:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio).lower()
                    
                    if "stop" in text or "close" in text or "deactivate" in text:
                        speak_async("Closing scanner.")
                        running = False
                        break
                except: pass
        except: pass

# --- MAIN LOOP (NO MEDIAPIPE) ---
def start_sign_scanning():
    global running, last_spoken_time
    
    # 1. Start Voice Listener
    listener_thread = threading.Thread(target=listen_for_stop)
    listener_thread.daemon = True
    listener_thread.start()

    # 2. Setup Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(3, 1280)
    cap.set(4, 720)

    speak_async("Scanner online. AI features disabled.")

    # Variables for simple motion detection
    _, prev_frame = cap.read()
    prev_frame = cv2.flip(prev_frame, 1)
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    while running:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # --- SIMPLE MOTION DETECTION (Since AI is broken) ---
        # This calculates the difference between the last frame and this frame
        diff = cv2.absdiff(prev_gray, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # If there is a lot of motion (white pixels in thresh), alert
        motion_amount = np.sum(thresh)
        if motion_amount > 1000000: # Sensitivity
            cv2.putText(frame, "MOTION DETECTED", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

        # Update previous frame
        prev_gray = gray

        # --- HUD ---
        cv2.putText(frame, "JARVIS SYSTEM: ONLINE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # ERROR WARNING ON SCREEN
        cv2.putText(frame, "NOTE: Hand AI requires Python 3.11", (50, 650), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "Currently running in LITE MODE", (50, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("JARVIS SIGN SCANNER (LITE)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_sign_scanning()