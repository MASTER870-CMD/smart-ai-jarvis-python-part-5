import cv2
import time
import threading
import random
import speech_recognition as sr
import pyttsx3

# --- CONFIGURATION ---
running = True

# --- VOICE OUTPUT ---
engine = pyttsx3.init()
def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except: pass

# --- VOICE INPUT (THREADED) ---
def listen_for_stop():
    global running
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    while running:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Listen specifically for stop commands
                try:
                    # Short timeout to keep the loop checking 'running' status
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio).lower()
                    print(f"[Vision Listener]: {text}")
                    
                    if "stop" in text or "close" in text or "deactivate" in text:
                        speak("Deactivating vision system.")
                        running = False
                        break
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
        except:
            pass

# --- MAIN VISION LOOP ---
def start_face_scanning():
    global running
    
    # 1. Start Voice Listener Thread for "Stop" command
    listener_thread = threading.Thread(target=listen_for_stop)
    listener_thread.daemon = True
    listener_thread.start()

    # 2. Setup Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(3, 1280) # Width
    cap.set(4, 720)  # Height

    # 3. Load Face Detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    speak("Face detection online.")

    # Simulated Data for "Mock" Analysis 
    # (Real age/gender/mood AI models are too heavy (2GB+) for this script, 
    # so we simulate the analysis to look cool like Iron Man)
    moods = ["Focused", "Neutral", "Happy", "Serious", "Calm"]
    genders = ["Male", "Female"]
    last_analysis_time = 0
    current_mood = "Scanning..."
    current_age = "..."
    current_gender = "..."

    while running:
        ret, frame = cap.read()
        if not ret: break

        # Mirror the frame
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

        # --- DRAW HUD ---
        for (x, y, w, h) in faces:
            # 1. Box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
            
            # 2. Tech Corners
            cv2.line(frame, (x, y), (x+20, y), (0, 255, 255), 4)
            cv2.line(frame, (x, y), (x, y+20), (0, 255, 255), 4)
            cv2.line(frame, (x+w, y+h), (x+w-20, y+h), (0, 255, 255), 4)
            cv2.line(frame, (x+w, y+h), (x+w, y+h-20), (0, 255, 255), 4)
            
            # 3. Simulated Analysis (Updates every 2 seconds)
            if time.time() - last_analysis_time > 2.0:
                current_mood = random.choice(moods)
                current_age = str(random.randint(22, 35)) # Mock age
                current_gender = random.choice(genders)   # Mock gender
                last_analysis_time = time.time()

            # 4. Display Stats
            label_x = x + w + 10
            # Ensure label doesn't go off screen
            if label_x > 1100: label_x = x - 200

            cv2.putText(frame, f"TARGET: HUMAN", (label_x, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"GENDER: {current_gender}", (label_x, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            cv2.putText(frame, f"AGE EST: {current_age}", (label_x, y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            cv2.putText(frame, f"MOOD: {current_mood}", (label_x, y + 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

        # --- SYSTEM STATUS OVERLAY ---
        cv2.putText(frame, "JARVIS VISION SYSTEM: ONLINE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, "SAY 'STOP SCANNING' TO EXIT", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("JARVIS FACE SCANNER", frame)

        # Quit if 'q' is pressed manually
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_face_scanning()