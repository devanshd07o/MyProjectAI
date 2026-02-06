import sys
import os
import json
import pyaudio
import subprocess
import socket
import time
import keyboard  # <--- Keys ke liye
from vosk import Model, KaldiRecognizer

# --- ⚙️ CONFIGURATION ---
MODEL_PATH = "model"
SAMPLE_RATE = 16000
TARGET_SCRIPT = "FinalAI.py"
LOCK_PORT = 55555

# --- 🧠 SINGLE INSTANCE CHECK ---
def check_if_already_running():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', LOCK_PORT))
        return s
    except socket.error:
        print("\n⚠️ INFERNA IS ALREADY RUNNING!")
        time.sleep(2)
        sys.exit()

instance_lock = check_if_already_running()

# --- 🎭 THE WAKE WORD MATRIX (NOT REDUCED) ---
WAKE_WORD_ALIASES = [
    # --- 1. ORIGINAL PHONETIC LIST ---
    "inferna", "inferno", "in fer na", "in fern a", "internal",
    "environment", "hey environment", "environmental",
    "in vermont", "in burma", "inverness",
    "in burner", "hey burner", "kane burner", "kane butler", "burner",
    "in fatima", "hey fatima", "fatima",
    "foreigner", "hey foreigner", "in foreigner", "and foreigner",
    "international", "invite now", "he invited me",
    "nine hundred", "in my now",
    "for dinner", "in dinner","in verona","hello",
    "in fact now", "in fact me", "in right now", "in fighting now",

    # --- 2. COMMAND & AI PREFIXES ---
    "command inferna", "nexus inferna", "project inferna", 
    "active inferna", "status inferna", "system inferna",
    "hello inferna", "wake up inferna", "master inferna",
    "cyber inferna", "global inferna", "rapid inferna",
    "delta inferna", "direct inferna", "matrix inferna",

    # --- 3. HINDI INFALLIBLE TRIGGERS ---
    "aadesh inferna", "adesh inferna", "aadesh",
    "sanket inferna", "sanket",
    "shakti inferna", "shakti",
    "pratham inferna", "pratham",
    "suno inferna", "sun rahi ho",

    # --- 4. SHARP AI KEYWORDS ---
    "jarvis", "cortex", "titan", "cipher", "aura"
]

# --- 🧠 LOAD VOSK BRAIN ---
if not os.path.exists(MODEL_PATH):
    print(f"❌ Error: '{MODEL_PATH}' folder nahi mila.")
    sys.exit()

print(f"\n🚀 Loading VOSK Launcher... (Please wait)")
try:
    model = Model(MODEL_PATH)
except Exception as e:
    print(f"❌ Model Load Error: {e}")
    sys.exit()

def get_pyaudio_stream():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=8000)
    return p, stream

rec = KaldiRecognizer(model, SAMPLE_RATE)
p, stream = get_pyaudio_stream()
stream.start_stream()

print("\n" + "="*50)
print("🟢 GUARD ACTIVE (Waiting for Voice or Ctrl+Alt+Shift)...")
print("="*50 + "\n")

# --- 🚀 THE MAIN ENGINE ---
while True:
    try:
        # --- 1. KEYBOARD CHECK (100% RELIABLE) ---
        if keyboard.is_pressed('ctrl+alt+shift'):
            print("\n⌨️ KEY TRIGGER! Launching AI...")
            while keyboard.is_pressed('ctrl+alt+shift'): pass 
            
            stream.stop_stream(); stream.close(); p.terminate()

            try:
                subprocess.run(["py", "-3.12", TARGET_SCRIPT], check=True)
            except Exception as e: print(f"Error: {e}")

            # Restart Guard
            rec = KaldiRecognizer(model, SAMPLE_RATE)
            p, stream = get_pyaudio_stream()
            stream.start_stream()
            print("🟢 GUARD ACTIVE...")
            continue

        # --- 2. VOICE CHECK (OPTIMIZED & SENSITIVE) ---
        data = stream.read(4000, exception_on_overflow=False)
        if len(data) == 0: break

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result['text'].lower()

            if text:
                print(f"👂 Suna: {text}")
                
                # Check if ANY alias is hidden inside the heard text
                if any(alias in text for alias in WAKE_WORD_ALIASES):
                    print("\n🔥 VOICE TRIGGER! Launching AI...")
                    
                    stream.stop_stream(); stream.close(); p.terminate()

                    try:
                        subprocess.run(["py", "-3.12", TARGET_SCRIPT], check=True)
                    except Exception as e: print(f"Error: {e}")

                    print("\n🔄 Restarting Guard...")
                    rec = KaldiRecognizer(model, SAMPLE_RATE)
                    p, stream = get_pyaudio_stream()
                    stream.start_stream()
                    print("🟢 GUARD ACTIVE...")

    except KeyboardInterrupt:
        print("\n🛡️ Guard Shielded. Close window to stop.")
        continue
    except Exception as e:
        # Auto-restart on stream crash
        try: stream.stop_stream(); stream.close(); p.terminate()
        except: pass
        p, stream = get_pyaudio_stream()
        stream.start_stream()