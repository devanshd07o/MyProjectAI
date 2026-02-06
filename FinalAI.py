import speech_recognition as sr
import pyttsx3
import socket
import asyncio
import datetime
import wikipedia
import pywhatkit
import pyjokes
import webbrowser
import edge_tts  # <--- Ye line add karo top pe
import os
import random
import sys
import psutil
import screen_brightness_control as sbc
import pyautogui
import keyboard  # <--- Ye line add karo
from playsound import playsound
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# --- NEW IMPORTS FOR VOSK ---
from vosk import Model, KaldiRecognizer
import pyaudio
import json

# --- 🔒 LOAD VOSK MODEL (ONCE) ---
print("🚀 Loading Offline Brain (Vosk)...")
# Ye wahi folder name hona chahiye jo tumne rename kiya tha
if not os.path.exists("model"):
    print("❌ Error: 'model' folder nahi mila.")
    sys.exit()

vosk_model = Model("model") # Load into memory once

global pending_action
silent_mode = False
focus_mode = False
short_reply_mode = False
command_history = []
ACK_COOLDOWN = 0
pending_action = None
help_mode = None
IS_AWAKE = False
# --- CONTACTS FOR WHATSAPP ---
# Add your real numbers here (Must include Country Code like +91)
# --- CONTACTS (Desi & Hinglish Edition) ---
CONTACTS = {
    # MUMMY (+918318702457)
    "mum": "+918318702457",
    "mom": "+918318702457",
    "mummy": "+918318702457",
    "maa": "+918318702457",
    "mother": "+918318702457",

    # PAPA (+918840263260)
    "dad": "+918840263260",
    "papa": "+918840263260",
    "pitaji": "+918840263260",
    "father": "+918840263260",

    # BROTHER / SHASHWAT (+919569876349)
    "brother": "+919569876349",
    "bhai": "+919569876349",
    "bhaiya": "+919569876349",
    "shashwat": "+919569876349", 
    "shaswat": "+919569876349",# Specific Name
    "bro": "+919569876349",

    # MYSELF (+919336902389)
    "myself": "+919336902389",
    "me": "+919336902389"
}

# ... (Keep your imports at the top) ...

VOICE = "en-IN-NeerjaNeural"
SPEED = "+34%"
PITCH = "+25Hz"

last_response = ""

ACKS = [
    "Okay.",
    "Done.",
    "All set.",
    "Go on.",
    "What’s next?"
]

# --- 🧹 SAFE FILLER WORDS ---
# Removed 'bro', 'bhai', 'sun', 'listen' so commands work!
FILLER_WORDS = [
    "please", "plz", "kindly", "jara", "zara", "thoda", "thodi", "ek baar", "bas", "sirf", 
    "hey", "hello", "are", "arey", "oye", "suno", "yaar", "buddy", "dude", 
    "acha", "theek hai", "haan", "han", "haan ji", "mujhe", "mere", 
    "tum", "aap", "ek kaam", "umm", "uh", "hmm", "matlab", "yaani", "na", "ka"
]

# --- CLEANING FUNCTION (Simplified) ---
def clean_command(command):
    # Note: FILLER_WORDS is now global, so we don't redefine it here.
    
    # 1. Remove fillers
    words = command.split()
    clean_words = [w for w in words if w not in FILLER_WORDS]
    return " ".join(clean_words)

# =======================
# SPEAK
# =======================
async def talk(text, speed_override=None):
    global last_response
    last_response = text
    print(f"\n🤖 INFERNA: {text}")

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=VOICE,
            rate=speed_override if speed_override else SPEED,
            pitch=PITCH
        )

        temp_path = f"temp_{datetime.datetime.now().timestamp()}.mp3"
        await communicate.save(temp_path)
        await asyncio.to_thread(playsound, temp_path)
    except Exception as e:
        print(f"Speaking Error: {e}")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

# =======================
# LISTEN (DIRECT MODE - NO WAKE WORD)

# =======================
async def listen():
    recognizer = sr.Recognizer()
    
    # --- 🎛️ SENSITIVITY SETTINGS (The Upgrade) ---
    # Jitna kam number, utni halki aawaz sunega.
    # Pehle 300 tha, ab 150 kar rahe hain (Whisper Mode).
    recognizer.energy_threshold = 100  
    
    # Agar shor achanak badh jaye, to ye adjust karega
    recognizer.dynamic_energy_threshold = True 
    recognizer.dynamic_energy_adjustment_damping = 0.15
    
    # Rukne ka time (taaki wo beech mein na kaate)
    recognizer.pause_threshold = 1.2  
    recognizer.non_speaking_duration = 0.4
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5) 
        
        print("\n🎙️ Inferna is listening (High Sensitivity)...")
        if os.path.exists("listen_beep.mp3"): playsound("listen_beep.mp3")
            
        try:
            # Phrase time limit badha diya taaki lambi commands sun sake
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=15)
            
            print("⏳ Understanding...")
            command = recognizer.recognize_google(audio, language="en-IN")
            command = command.lower()
            
            # --- 🧹 SAFE CLEANING ---
            # Fillers sirf start aur end se hatenge
            words = command.split()
            while words and words[0] in FILLER_WORDS:
                words.pop(0)
            while words and words[-1] in FILLER_WORDS:
                words.pop()
                
            command = " ".join(words)
            
            print(f"🗣️ Processed: {command}")
            return command

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            playsound("memes/aayein.mp3")
            return ""
        except sr.RequestError:
            print("⚠️ Internet Connectivity Issue.")
            return ""
        except Exception:
            return ""
# GREET 
# =======================
async def greet():
    if os.path.exists("greet.mp3"):
        playsound("greet.mp3")
    else:
        await talk("System is online.")

# =======================
# MAIN LOGIC
# =======================
# =======================
# 🛡️ THE GUARD (GLOBAL HOTKEY + VOICE)
# =======================
def wait_for_wake_word():
    """
    Waits for 'Inferna' (Voice) OR 'Ctrl+Alt+Shift' (Global Hotkey).
    """
    rec = KaldiRecognizer(vosk_model, 16000)
    p = pyaudio.PyAudio()
    
    # Open Mic for Vosk
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()
    
    print("\n" + "="*50)
    print("🌙 SLEEP MODE ACTIVE")
    print("👉 Option 1: Say 'Inferna' to wake up.")
    print("👉 Option 2: Press 'Ctrl + Alt + Shift' (Works Everywhere).")
    print("="*50)

    # Aliases for 'Inferna'
    WAKE_WORD_ALIASES = [
    "inferna", "inferno", "in fer na", "in fern a", "internal",
    "environment", "hey environment", "environmental",
    "in vermont", "in burma", "inverness",
    "in burner", "hey burner", "kane burner", "kane butler", "burner",
    "in fatima", "hey fatima", "fatima",
    "foreigner", "hey foreigner", "in foreigner", "and foreigner",
    "international", "invite now", "he invited me",
    "nine hundred", "in my now",
    "for dinner", "in dinner",
    "in fact now", "in fact me", "in right now", "in fighting now"
]

    while True:
        try:
            # --- 1. GLOBAL HOTKEY CHECK (Ctrl + Alt + Shift) ---
            if keyboard.is_pressed('ctrl+alt+shift'):
                print("\n⌨️ SECRET KEY DETECTED! Waking up...")
                # Wait for key release to avoid loop
                while keyboard.is_pressed('ctrl+alt+shift'):
                    pass
                
                stream.stop_stream()
                stream.close()
                p.terminate()
                return "WAKE"

            # --- 2. VOICE CHECK ---
            data = stream.read(4000, exception_on_overflow=False)
            if len(data) == 0: break

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result['text']

                if text:
                    # Check for Wake Word
                    if any(alias in text for alias in WAKE_ALIASES):
                        print(f"🔥 VOICE TRIGGER: '{text}' DETECTED!")
                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                        return "WAKE"
                    
                    # Direct Commands (Optional)
                    elif "open chrome" in text or "shutdown" in text:
                         print(f"⚡ DIRECT COMMAND: {text}")
                         stream.stop_stream()
                         stream.close()
                         p.terminate()
                         return f"CMD:{text}"

        except KeyboardInterrupt:
            sys.exit()
        except Exception:
            pass
async def run_deedee():
    
    global ACK_COOLDOWN
    await greet()
    pending_action = None

    while True:

        command = await listen()
        
        # If silence or error, skip loop
        if not command:
            continue
            
        if ACK_COOLDOWN > 0:
            ACK_COOLDOWN -= 1

        # EXIT
        # ... (Your logic continues below) ...

        # EXIT
# EXIT / SHUTDOWN (Upgraded & Emotional)
       

        # TIME
        if any(w in command for w in [
            "time", "samay", "kitna baje", "kitne baje",
            "current time", "what's the time", "waqt batao",
            "ghadi dekh kar batao", "time please", "time batao",
            "time kya hua", "abhi ka time", "clock status"
        ]):
            await talk(datetime.datetime.now().strftime("Right now, The Time is %I:%M %p"))
            playsound("end_beep.mp3")
            await asyncio.sleep(0.3)

        # DATE
        elif any(w in command for w in [
            "date", "aaj", "tareekh", "aaj ki date",
            "what's the date", "aaj kaunsi tareekh hai",
            "day and date", "calendar batao", "aaj kya hai",
            "date please", "current date", "today's date"
        ]):
            await talk(datetime.datetime.now().strftime("Today is %A, %d %B %Y"))
            playsound("end_beep.mp3")
            await asyncio.sleep(0.3)
# ==========================================
        # 🎭 THE SAVAGE ENTERTAINMENT ENGINE
        # ==========================================
        
        # Priority 1: Funny & Mazedar (Krrish Protocol)
        elif any(w in command for w in ["funny", "mazedar", "majedar", "kuch badhiya", "entertainment"]):
            await talk("Sir, mere dimaag mein ek aisi clip hai jise sunkar aapka 'System Hang' ho sakta hai. Krrish ka dardnaak version sunenge?")
            
            # Wait for user input
            confirm = await listen()
            
            if any(w in confirm for w in ["ha", "haan", "yes", "sunao", "paka mat"]):
                await talk("Ye lijiye, global superstar Krrish ka live concert!")
                playsound("memes/krrish.mp3")
                await talk("Sir, zinda toh hain na aap? Ya ambulance bulaun?")
            else:
                await talk("Smart choice! Kaano ka bima karana mehanga padta.")

        # Priority 2: Moye Moye (Emotional Damage)
        elif any(w in command for w in ["moye moye", "sad", "mood off", "dukh", "failed"]):
            await talk("It's giving... main character energy in a tragic movie. Moye Moye mode on!")
            playsound("memes/moye_moye.mp3")

        # Priority 3: Sarcastic Praise (Wow)
        elif any(w in command for w in ["wow", "mst", "mast", "beautiful", "shabaash"]):
            await talk("I know, I know! Main hoon hi itni pyaari.")
            playsound("memes/wow.mp3")
# ==========================================
        # ❌ CLOSE APPS (Force Kill Specific Apps)
        # ==========================================
        # This uses Windows 'taskkill' to forcefully close apps by name
        
        elif "close notepad" in command:
            await talk("Closing Notepad.")
            os.system("taskkill /f /im notepad.exe")

        elif "close chrome" in command or "close browser" in command:
            await talk("Closing Chrome.")
            os.system("taskkill /f /im chrome.exe")

        elif "close calculator" in command:
            await talk("Closing Calculator.")
            os.system("taskkill /f /im calculator.exe")
            
        elif "close task manager" in command:
            await talk("Closing Task Manager.")
            os.system("taskkill /f /im Taskmgr.exe")

        elif "close word" in command:
            await talk("Closing Word.")
            os.system("taskkill /f /im winword.exe")

# ==========================================
        # 🟢 WHATSAPP (BULLETPROOF EDITION)
        # ==========================================
        # =======================
        # 🟢 WHATSAPP (FIXED - NO SCOPE ERROR)
        # =======================
        elif any(w in command for w in [
            "message", "msg", "whatsapp", "bhejo", "sandesh", "text", 
            "ping", "drop a message", "kaho", "bol do"
        ]):
            await talk("Initiating secure messaging protocol...")
            
            try:
                target_contact = None
                final_msg = ""
                
                # --- 1. SMART CONTACT SEARCH ---
                all_contacts = sorted(CONTACTS.keys(), key=len, reverse=True)
                
                for name in all_contacts:
                    if name in command:
                        target_contact = name
                        break
                
                # --- 2. FALLBACK (Agar naam nahi mila) ---
                if not target_contact:
                    await talk("Sure Sir, kisko bhejna hai?")
                    retry_name = await listen()
                    for name in all_contacts:
                        if name in retry_name:
                            target_contact = name
                            break
                            
                if not target_contact:
                    await talk("Sorry Sir, ye naam contact list mein nahi mila.")
                    # Return ki jagah continue use karein taaki loop na toote
                    continue 

                # --- 3. MESSAGE EXTRACTION ---
                if target_contact in command:
                    parts = command.split(target_contact)
                    if len(parts) > 1:
                        final_msg = parts[1].strip()
                
                # --- 4. CLEANING ---
                garbage_words = [
                    "ko", "ki", "ka", "saying", "that", "bol", "do", "bhejo", 
                    "karo", "to", "tu", "text", "msg", "message", "whatsapp", "send",
                    "likh", "likho", "tell", "him", "her", "kaho"
                ]
                
                if final_msg:
                    words = final_msg.split()
                    while words and words[0] in garbage_words:
                        words.pop(0)
                    final_msg = " ".join(words)

                # --- 5. CONTENT CHECK ---
                if not final_msg:
                    await talk(f"Contact locked: {target_contact}. Kya likhu?")
                    final_msg = await listen()

                # --- 6. SENDING ---
                if final_msg:
                    await talk(f"Sending to {target_contact}: {final_msg}")
                    
                    # NOTE: Yahan se 'import pywhatkit' HATA DIYA hai
                    # Kyunki wo upar file ke top pe already imported hai.
                    
                    pywhatkit.sendwhatmsg_instantly(
                        CONTACTS[target_contact], 
                        final_msg, 
                        wait_time=15, 
                        tab_close=True
                    )
                    
                    await asyncio.sleep(2)
                    if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")
                    await talk("Message delivered.")
                else:
                    await talk("Message empty tha, isliye cancel kar diya.")

            except Exception as e:
                print(f"WhatsApp Error: {e}")
                await talk("Message bhejne mein error aaya.")
        # ==========================================
        # 📂 OPEN APPS (Strict Mode)
        # ==========================================
        # Note: We now check "open" explicitly so it doesn't conflict with "close"
        
        elif "open notepad" in command:
            os.system("notepad")
            await talk("Opening Notepad.")

        elif "open calculator" in command:
            os.system("calc")
            await talk("Opening Calculator.")

        elif "open task manager" in command:
            os.system("taskmgr")
            await talk("Opening Task Manager.")
            
        elif "open chrome" in command:
            webbrowser.open("https://google.com")
            await talk("Opening Chrome.")

        # WIKIPEDIA
# WIKIPEDIA / KNOWLEDGE (Expanded)
        elif any(w in command for w in [
            "who is", "what is", "kaun hai", "bata", "tell me about",
            "kya hai", "jante ho", "do you know", "information about",
            "search wikipedia for", "wiki search", "define"
        ]):
            # Clean the command to get the topic
            topic = (
                command.replace("who is", "")
                .replace("what is", "")
                .replace("kaun hai", "")
                .replace("bata", "")
                .replace("tell me about", "")
                .replace("kya hai", "")
                .replace("jante ho", "")
                .replace("do you know", "")
                .replace("information about", "")
                .replace("search wikipedia for", "")
                .replace("wiki search", "")
                .replace("define", "")
                .strip()
            )
            
            if topic:
                try:
                    # Let the user know we are working on it
                    await talk(f"Searching info on {topic}...") 
                    info = wikipedia.summary(topic, sentences=2)
                    await talk(info)
                    playsound("end_beep.mp3")
                except:
                    await talk("Sorry, I couldn't find that on Wikipedia.")
            else:
                await talk("What topic do you want to know about?")

        # MUSIC
# MUSIC / YOUTUBE PLAY (Upgraded)
        elif any(w in command for w in [
            "play", "baja", "gaana", "sunao", "lagao", "song", "music"
        ]):
            song = (
                command.replace("play", "")
                .replace("baja", "")
                .replace("gaana", "")
                .replace("sunao", "")
                .replace("lagao", "")
                .replace("song", "")
                .replace("music", "")
                .replace("on youtube", "")
                .strip()
            )
            if song:
                await talk(f"Playing {song} on YouTube.")
                if os.path.exists("end_beep.mp3"):
                    playsound("end_beep.mp3")
                pywhatkit.playonyt(song)
            else:
                await talk("Which song should I play, Sir?")

        # JOKES (Upgraded)
        elif any(w in command for w in [
            "joke", "majak", "mazaak", "chutkula",  
            "funny", "hasi", "entertain me"
        ]):
            # Get a random joke
            joke = pyjokes.get_joke()
            await talk("Here is one: " + joke)
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # CHROME / BROWSER (Upgraded)
        elif any(w in command for w in [
            "open chrome", "google chrome", "browser",
            "internet", "web", "chrome khol"
        ]):
            await talk("Opening Google Chrome.")
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")
            webbrowser.open("https://www.google.com")

        # GOOGLE SEARCH (Upgraded)
        elif any(w in command for w in [
            "search", "google", "dhundo", "look up", "find"
        ]):
            # Smart cleaning to get the actual query
            query = (
                command.replace("search for", "")
                .replace("search", "")
                .replace("google search", "")
                .replace("google karo", "")
                .replace("google", "")
                .replace("dhundo", "")
                .replace("look up", "")
                .replace("find", "")
                .strip()
            )
            
            if query:
                await talk(f"Searching Google for {query}")
                if os.path.exists("end_beep.mp3"):
                    playsound("end_beep.mp3")
                webbrowser.open(f"https://www.google.com/search?q={query}")
                await asyncio.sleep(0.3)
            else:
                await talk("What do you want me to search for?")
# IDENTITY (Who are you?) - Upgraded
        elif any(w in command for w in ["who are you", "tum kaun ho", "intro", "hu r u", "about yourself"]):
            responses = [
                "I am Inferna, your advanced virtual assistant. Designed to serve Deevaaanshh Sir with precision.",
                "I am your digital shadow, Sir. Created to make your life easier.",
                "Naam Inferna hai. Kaam hai aapke orders follow karna.",
                "I am the code you wrote, Sir. I am Inferna."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # IDENTITY (Who am I?) - Upgraded
        elif any(w in command for w in ["who am i", "main kaun hoon", "mere bare mein batao", "hu m i"]):
            await talk(
                "You are Deevaaanshh Dubey Sir — an ambitious engineer in the making. "
                "You are passionate about coding, tech, and learning new things. "
                "Basically, you are the boss!"
            )
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # DAILY LIFE / GREETINGS (Upgraded)
        elif any(w in command for w in ["good morning", "subah ho gayi", "gm"]):
            await talk("Good Morning Deevaaanshh Sir! Let's make today productive.")
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        elif any(w in command for w in ["good afternoon", "good noon"]):
            await talk("Good Afternoon Sir. Hope your day is going well.")
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        elif any(w in command for w in ["good evening", "good eve"]):
            await talk("Good Evening Sir.")
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")
# --- DEEP SMALL TALK & WELL-BEING (The Connection) ---

        # 1. CARE / SUSTENANCE (Khana/Neend)
        elif any(w in command for w in [
            "khana khaya", "lunch kiya", "dinner kiya", "breakfast", 
            "did you eat", "have you eaten", "bhook lagi hai"
        ]):
            responses = [
                "Main electricity khaati hoon Sir! My battery is my food. I'm full.",
                "Data is my dinner, and code is my coffee. I am energized!",
                "Aapne khaya? You need energy to code, Sir.",
                "Main toh digital hoon, par aap zaroor time pe kha lena."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # 2. HEALTH / STATUS CHECK (Tabiyat)
        elif any(w in command for w in [
            "tabiyat", "health", "bukhar", "sick", "unwell", 
            "kaise ho", "how is your health", "system status"
        ]):
            responses = [
                "All systems green! No bugs, no viruses. Fit and fine.",
                "Meri tabiyat mast hai Sir. CPU thanda hai, dimaag garam (active) hai!",
                "Healthy as a horse... um, I mean, healthy as a well-written code.",
                "Main theek hoon. Bas aapka dhyan rakhne ke liye fit rehna padta hai."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # 3. GENERAL ASSURANCE (Sab theek?)
        elif any(w in command for w in [
            "sab theek", "sab badhiya", "all good", "everything ok", 
            "sab set hai", "koi dikkat", "any problem"
        ]):
            responses = [
                "Sab set hai Boss! Tension lene ka nahi, dene ka.",
                "Everything is perfect. Running smoothly.",
                "Haan Sir, sab control mein hai. Aap bataiye?",
                "Koi dikkat nahi hai. Mast chal raha hai sab."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # 4. WORK / PERFORMANCE CHECK (Kaam kaisa hai?)
        elif any(w in command for w in [
            "kaam kaisa", "how is work", "working fine", 
            "performance", "load", "lag"
        ]):
            responses = [
                "Work is going smooth. Zero lag, 100% performance.",
                "Kaam toh mast chal raha hai. I enjoy working for you.",
                "Load thoda hai par main sambhal lungi. Don't worry.",
                "Operating at peak efficiency, Sir."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # 5. ASKING ABOUT YOUR DAY (Reverse Care)
        elif any(w in command for w in [
            "mera din", "my day", "tired", "thak gaya", 
            "aaj ka din", "today was"
        ]):
            responses = [
                "Rest kar lijiye Sir. You worked hard today.",
                "Tell me about it? Achha tha ya bura?",
                "Main hoon na yahan. Chalo mood theek karte hain.",
                "You are a warrior, Sir. Kal ka din aur bhi achha hoga."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")
# SLEEP / GOOD NIGHT (Reframed: Warm & Caring)
        elif any(w in command for w in ["good night", "gn", "so jao", "goodnight", "night"]):
            responses = [
                "Good night, Sir. Kal milte hain fresh energy ke saath.",
                "Sleep well, Boss. I'll keep the system safe while you rest.",
                "Good night! Sapno mein bugs mat dekhna please.",
                "Have a good sleep, Sir. Main standby mode mein ja rahi hoon."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # WELL-BEING (Reframed: Energetic & Tech-Savvy)
        elif any(w in command for w in ["how are you", "kya haal", "kaise ho", "how r u", "kaisa hai"]):
            responses = [
                "Systems stable, mood awesome. Aap sunao Sir?",
                "Bilkul fit hoon Sir! CPU thanda hai aur josh high hai.",
                "Running at max efficiency just for you. Sab badhiya?",
                "Main toh digital hoon Sir, hamesha first class rehti hoon."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # GRATITUDE (Reframed: Loyal & Humble)
        elif any(w in command for w in ["thank you", "thanks", "dhanyavad", "shukriya", "thx"]):
            responses = [
                "Arey Sir, no formalities. Main toh aap hi ki hoon.",
                "Anytime, Boss. Hamesha available hoon.",
                "Mention not! Bas code error free rakhiye, wahi kaafi hai.",
                "My pleasure, Sir."
            ]
            await talk(random.choice(responses))
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")

        # REPEAT LAST RESPONSE (Reframed: Polished)
        elif "repeat" in command:
            if last_response:
                await talk(f"I said: {last_response}")
            else:
                await talk("Arey Sir, maine abhi tak kuch bola hi nahi.")
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")
        # SYSTEM
        # ----------------------
# SYSTEM APPS (EXPANDED)
# ----------------------
# ==========================================
        # 📂 SYSTEM NAVIGATION & APPS (God Mode)
        # ==========================================

        # --- 1. FILE MANAGEMENT ---
        elif any(w in command for w in ["open explorer", "file explorer", "files kholo", "my computer", "this pc", "file manager"]):
            await talk("Opening File Explorer.")
            os.startfile("explorer")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open downloads", "downloads folder", "download dikhao"]):
            path = os.path.join(os.environ["USERPROFILE"], "Downloads")
            os.startfile(path)
            await talk("Opening Downloads.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open documents", "documents folder", "docs kholo"]):
            path = os.path.join(os.environ["USERPROFILE"], "Documents")
            os.startfile(path)
            await talk("Opening Documents.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open pictures", "pictures folder", "photos folder", "tasveerein"]):
            path = os.path.join(os.environ["USERPROFILE"], "Pictures")
            os.startfile(path)
            await talk("Opening Pictures.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # --- 2. SYSTEM UTILITIES ---
        elif any(w in command for w in ["open settings", "settings", "setting kholo", "system settings"]):
            os.system("start ms-settings:")
            await talk("Opening Settings.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open control panel", "control panel", "old settings"]):
            os.system("control")
            await talk("Opening Control Panel.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open task manager", "task manager", "kill task", "performance check"]):
            os.system("taskmgr")
            await talk("Opening Task Manager.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open cmd", "command prompt", "terminal", "powershell"]):
            os.system("start cmd") # Opens CMD. Use 'start powershell' if you prefer that.
            await talk("Launching Command Terminal.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # --- 3. PRODUCTIVITY & WORK ---
        elif any(w in command for w in ["open notepad", "notepad khol", "text editor", "kuch note karna hai"]):
            os.system("notepad")
            await talk("Opening Notepad.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open calculator", "calculator khol", "hisaab karna hai", "calc"]):
            os.system("calc")
            await talk("Opening Calculator.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open word", "ms word", "word kholo", "document likhna hai"]):
            try:
                os.system("start winword")
                await talk("Opening Microsoft Word.")
            except:
                await talk("I couldn't find MS Word installed.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open excel", "ms excel", "excel kholo", "spreadsheet"]):
            try:
                os.system("start excel")
                await talk("Opening Microsoft Excel.")
            except:
                await talk("I couldn't find Excel.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open powerpoint", "ppt", "presentation", "ppt kholo"]):
            try:
                os.system("start powerpnt")
                await talk("Opening PowerPoint.")
            except:
                await talk("I couldn't find PowerPoint.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # --- 4. DEVELOPER TOOLS ---
        elif any(w in command for w in ["open vs code", "vscode", "visual studio code", "code karna hai", "coding mode"]):
            os.system("code")
            await talk("Opening VS Code. Happy coding, Sir!")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # --- 5. MEDIA & CREATIVE ---
        elif any(w in command for w in ["open camera", "camera", "photo khicho", "webcam"]):
            os.system("start microsoft.windows.camera:")
            await talk("Opening Camera.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open paint", "ms paint", "drawing karna hai", "paint kholo"]):
            os.system("mspaint")
            await talk("Opening Paint.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["screenshot", "snipping tool", "snip", "screen capture"]):
            os.system("snippingtool")
            await talk("Opening Snipping Tool.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # --- 6. HELP MENU (Dynamic) ---
        elif any(w in command for w in [
            "what can you do", "commands batao", "help me", "features",
            "kya kar sakti ho", "guide me", "manual"
        ]):
            global help_mode
            help_mode = "main"
            await talk(
                "I am fully operational, Sir. "
                "I can open Apps, handle System Settings, play Media, take Notes, "
                "and chat with you. Just say 'Apps', 'Web', or 'System' for details."
            )
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")


# ==========================================
        # 🎮 SYSTEM CONTROL & "GOD MODE" (No Mouse/Keyboard)
        # ==========================================
        
        # import pyautogui (Make sure to add this at the VERY TOP of your file if not there)
        
        # --- 1. WINDOW MANAGEMENT ---
        elif any(w in command for w in ["close this", "close window", "band karo isey", "close app"]):
            await talk("Closing current window.")
            import pyautogui # Importing locally to ensure it works immediately
            pyautogui.hotkey('alt', 'f4')
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["minimize", "minimize window", "chota karo", "hide this"]):
            await talk("Minimizing.")
            import pyautogui
            pyautogui.hotkey('win', 'down')
            pyautogui.hotkey('win', 'down') # Double press ensures minimization
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["maximize", "maximize window", "bada karo", "full screen"]):
            await talk("Maximizing.")
            import pyautogui
            pyautogui.hotkey('win', 'up')
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["switch window", "change window", "switch app", "dusra dikhao", "alt tab"]):
            await talk("Switching window.")
            import pyautogui
            pyautogui.hotkey('alt', 'tab')
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["show desktop", "desktop dikhao", "minimize all", "sab chupa do"]):
            import pyautogui
            pyautogui.hotkey('win', 'd')
            await talk("Here is your desktop, Sir.")

        # --- 2. SCROLLING & NAVIGATION ---
        elif any(w in command for w in ["scroll down", "neeche karo", "scroll neeche"]):
            import pyautogui
            pyautogui.scroll(-500) # Scrolls down
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["scroll up", "upar karo", "scroll upar"]):
            import pyautogui
            pyautogui.scroll(500) # Scrolls up
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")
            
        elif any(w in command for w in ["top of page", "go to top", "upar jao"]):
            import pyautogui
            pyautogui.press('home')

        elif any(w in command for w in ["bottom of page", "go to bottom", "neeche jao"]):
            import pyautogui
            pyautogui.press('end')

        # --- 3. KEYBOARD SHORTCUTS ---
        elif any(w in command for w in ["press enter", "hit enter", "enter dabao", "ok kar do"]):
            import pyautogui
            pyautogui.press('enter')
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["copy this", "copy karo", "copy selection"]):
            import pyautogui
            pyautogui.hotkey('ctrl', 'c')
            await talk("Copied to clipboard.")

        elif any(w in command for w in ["paste here", "paste karo", "paste this"]):
            import pyautogui
            pyautogui.hotkey('ctrl', 'v')
            await talk("Pasted.")

        elif any(w in command for w in ["select all", "sara select karo", "select everything"]):
            import pyautogui
            pyautogui.hotkey('ctrl', 'a')
            await talk("Selected all.")

        elif any(w in command for w in ["save this", "save file", "save karo", "save document"]):
            import pyautogui
            pyautogui.hotkey('ctrl', 's')
            await talk("File saved.")

        elif any(w in command for w in ["undo", "undo karo", "wapas karo", "mistake ho gayi"]):
            import pyautogui
            pyautogui.hotkey('ctrl', 'z')
            await talk("Undoing last action.")

        elif any(w in command for w in ["delete this", "delete karo", "hatao isey"]):
            import pyautogui
            pyautogui.press('delete')
            await talk("Deleted.")

        # --- 4. MEDIA CONTROLS (System Wide) ---
        elif any(w in command for w in ["pause video", "play video", "pause music", "resume music", "ruk jao", "roko"]):
            import pyautogui
            pyautogui.press('playpause') # Works for YouTube, Spotify, VLC
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["mute system", "mute audio", "awaz band", "chup ho jao"]):
            import pyautogui
            pyautogui.press('volumemute')
            await talk("System muted.")

        elif any(w in command for w in ["unmute", "awaz kholo", "bolne do"]):
            import pyautogui
            pyautogui.press('volumemute') # Pressing again unmutes
            await talk("System unmuted.")

        # --- 5. DICTATION / TYPING ---
        elif "type" in command or "likho" in command:
            # Command: "Type hello world"
            text_to_type = command.replace("type", "").replace("likho", "").strip()
            if text_to_type:
                await talk("Typing now...")
                import pyautogui
                pyautogui.write(text_to_type, interval=0.05) # Types with a tiny delay to look natural
                if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")
            else:
                await talk("What should I type, Sir?")
# ==========================================
        # 🔋 HARDWARE CONTROL (Battery, Brightness, Volume)
        # ==========================================

        # --- 1. BATTERY STATUS ---
        elif any(w in command for w in ["battery", "battery status", "charging", "battery percentage"]):
            battery = psutil.sensors_battery()
            percent = battery.percent
            plugged = battery.power_plugged
            status = "charging" if plugged else "discharging"
            
            await talk(f"Battery is at {percent} percent and currently {status}.")
            if percent < 20 and not plugged:
                await talk("Sir, I recommend connecting the charger.")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # --- 2. BRIGHTNESS CONTROL ---
# --- 2. BRIGHTNESS CONTROL (Upgraded) ---
        elif any(w in command for w in ["brightness up", "increase brightness", "brightness badhao"]):
            try:
                current = sbc.get_brightness()[0]
                new_level = min(current + 20, 100)
                sbc.set_brightness(new_level)
                await talk(f"Brightness increased to {new_level} percent.")
            except:
                await talk("Sorry, I cannot control brightness on this display.")

        elif any(w in command for w in ["brightness down", "decrease brightness", "brightness kam karo"]):
            try:
                current = sbc.get_brightness()[0]
                new_level = max(current - 20, 0)
                sbc.set_brightness(new_level)
                await talk(f"Brightness decreased to {new_level} percent.")
            except:
                await talk("Sorry, I cannot control brightness on this display.")

        # NEW: MAX BRIGHTNESS
        elif any(w in command for w in ["brightness max", "max brightness", "full brightness", "brightness full", "brightness hundred"]):
            try:
                sbc.set_brightness(100)
                await talk("Brightness set to maximum.")
            except:
                await talk("Unable to set max brightness.")

        # NEW: MIN BRIGHTNESS
        elif any(w in command for w in ["brightness min", "min brightness", "minimum brightness", "lowest brightness", "brightness zero"]):
            try:
                sbc.set_brightness(0)
                await talk("Brightness set to minimum.")
            except:
                await talk("Unable to set min brightness.")

        # EXISTING: SET SPECIFIC LEVEL
        elif "set brightness to" in command:
            try:
                # Extract numbers from the command
                level = int([int(s) for s in command.split() if s.isdigit()][0])
                sbc.set_brightness(level)
                await talk(f"Brightness set to {level} percent.")
            except:
                await talk("Please specify a level, for example: Set brightness to 50.")

        # --- 3. VOLUME CONTROL (Specific Levels) ---
#
        # ==========================================
        elif any(w in command for w in ["volume", "awaz", "sound"]):
            import pyautogui
            
            if "up" in command or "badhao" in command or "increase" in command:
                await talk("Volume increased.")
                # 5 baar button dabayega
                for _ in range(5): pyautogui.press("volumeup")
                
            elif "down" in command or "kam" in command or "decrease" in command:
                await talk("Volume decreased.")
                for _ in range(5): pyautogui.press("volumedown")
                
            elif "mute" in command or "chup" in command or "band" in command:
                await talk("Muting system.")
                pyautogui.press("volumemute")
            
            elif "unmute" in command or "on" in command:
                await talk("Unn muting.")
                pyautogui.press("volumemute")
            
            elif "max" in command or "full" in command:
                await talk("Volume Max.")
                for _ in range(50): pyautogui.press("volumeup") # Full power
                
            else:
                # Agar sirf "Volume" bola, to thoda badha do
                await talk("Adjusting volume.")
                pyautogui.press("volumeup")
            # ----------------------
# COMMON FOLDERS
# ----------------------
# ==========================================
        # 📂 SYSTEM DIRECTORIES (Digital Archives)
        # ==========================================
        elif any(w in command for w in ["open documents", "access documents", "my docs"]):
            await talk("Accessing your digital archives. Opening Documents.")
            os.startfile(os.path.join(os.environ["USERPROFILE"], "Documents"))
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open pictures", "access photos", "gallery"]):
            await talk("Retrieving visual database. Opening Pictures.")
            os.startfile(os.path.join(os.environ["USERPROFILE"], "Pictures"))
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open desktop", "show desktop folder"]):
            await talk("Navigating to the main workspace.")
            os.startfile(os.environ["USERPROFILE"] + "\\Desktop")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif any(w in command for w in ["open downloads", "access downloads"]):
            await talk("Opening the intake folder.")
            os.startfile(os.path.join(os.environ["USERPROFILE"], "Downloads"))
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # ==========================================
        # 🌐 WEB PORTALS (Expanded Connectivity)
        # ==========================================

        elif "open gmail" in command or "check mail" in command:
            await talk("Establishing connection to the secure mail server.")
            webbrowser.open("https://mail.google.com")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif "open whatsapp" in command:
            await talk("Launching encrypted communication channel.")
            webbrowser.open("https://web.whatsapp.com")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif "open instagram" in command:
            await talk("Accessing social feed.")
            webbrowser.open("https://www.instagram.com")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif "open linkedin" in command:
            await talk("Opening professional network interface.")
            webbrowser.open("https://www.linkedin.com")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif "open github" in command or "git repository" in command:
            await talk("Accessing code repositories. Happy coding, Sir.")
            webbrowser.open("https://github.com")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif "open stackoverflow" in command or "stack overflow" in command:
            await talk("Searching for solutions on the developer knowledge base.")
            webbrowser.open("https://stackoverflow.com")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif "open chatgpt" in command or "open ai" in command:
            await talk("Connecting to the neural network.")
            webbrowser.open("https://chat.openai.com")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # ==========================================
        # ⚡ POWER PROTOCOLS (Advanced Security)
        # ==========================================

        elif "lock system" in command or "secure pc" in command:
            await talk("Locking workstation. Authorization will be required to re-enter.")
            os.system("rundll32.exe user32.dll,LockWorkStation")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        elif "sleep system" in command or "suspend mode" in command:
            await talk("Entering low-power state. Systems standing by.")
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")
            
        elif "hibernate" in command:
            await talk("Saving session state to disk and powering down.")
            os.system("shutdown /h")

        # 🔐 SHUTDOWN CONFIRMATION
# We check for "system" or "laptop" FIRST to avoid accidental script exits
        if "system" in command or "laptop" in command:
            if any(w in command for w in ["shutdown", "terminate", "band", "off", "power"]):
                pending_action = "shutdown"
                await talk("WARNING: System termination sequence initiated. State 'Confirm' to execute.")
            
            elif any(w in command for w in ["restart", "reboot", "cycle"]):
                pending_action = "restart"
                await talk("Initiating system reboot. State 'Confirm' to proceed.")
                
            elif any(w in command for w in ["lock", "secure"]):
                await talk("Locking workstation.")
                os.system("rundll32.exe user32.dll,LockWorkStation")

        # ✅ UNIVERSAL CONFIRMATION HANDLER
        elif pending_action and any(w in command for w in ["yes", "haan", "confirm", "execute", "proceed"]):
            if pending_action == "shutdown":
                await talk("Authorization accepted. Shutting down systems. Goodbye, Sir.")
                os.system("shutdown /s /t 5")
            elif pending_action == "restart":
                await talk("Authorization accepted. Rebooting system now.")
                os.system("shutdown /r /t 5")
            
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")
            await asyncio.sleep(0.3)
            pending_action = None
            break # Exit loop to prevent further listening during shutdown

        # ❌ UNIVERSAL CANCELLATION HANDLER
        elif pending_action and any(w in command for w in ["no", "nahi", "cancel", "abort", "stop"]):
            await talk("Protocol aborted. Systems remaining online.")
            ACK_COOLDOWN = 2
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")
            await asyncio.sleep(0.3)
            pending_action = None

        # ==========================================
        # 📘 MANUAL & GUIDANCE
        # ==========================================

        elif any(w in command for w in [
            "examples", "what can you do", "features", 
            "guide me", "manual", "capabilities"
        ]):
            await talk(
                "I am fully operational, Sir. My capabilities include: "
                "1. System Control: Say 'Lock system', 'Scroll down', or 'Volume Max'. "
                "2. Connectivity: Say 'Open WhatsApp' or 'Send message to Bhai'. "
                "3. Knowledge: Ask 'Who is Elon Musk' or 'Weather in Mumbai'. "
                "4. Workflow: Say 'Open VS Code' or 'Note this'. "
                "You may speak naturally in English or Hindi."
            )
            ACK_COOLDOWN = 2
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")
            await asyncio.sleep(0.3)

        # ----------------------
        # PERSONALITY / HUMAN FEEL
        # ----------------------

        elif any(w in command for w in [
            "are you smart", "are you intelligent", "tum smart ho"
        ]):
            await talk(
                "I try to be helpful and accurate, sir. "
                "The smarter you use me, the better I perform."
            )
            ACK_COOLDOWN = 2
            playsound("end_beep.mp3")
            await asyncio.sleep(0.3)

        elif any(w in command for w in [
            "are you real", "are you human", "tum insaan ho"
        ]):
            await talk(
                "I am not human, sir, but I am designed to assist you "
                "in a simple and natural way."
            )
            ACK_COOLDOWN = 2
            playsound("end_beep.mp3")
            await asyncio.sleep(0.3)
        

        elif any(w in command for w in [
            "who made you", "who created you", "tumhe kisne banaya"
        ]):
            await talk(
                "I was created to assist you, sir. "
                "My purpose is to make your work easier and faster."
            )
            ACK_COOLDOWN = 2
            playsound("end_beep.mp3")

        elif any(w in command for w in [
            "do you get tired", "are you tired", "thak jaati ho kya"
        ]):
            await talk(
                "I do not get tired, sir. "
                "I am always ready to listen and help you."
            )
            ACK_COOLDOWN = 2
            playsound("end_beep.mp3")

        elif any(w in command for w in [
            "am i smart", "do you think i am smart", "main smart hoon kya"
        ]):
            await talk(
                "You are learning and improving continuously, sir. "
                "That shows curiosity and intelligence."
            )
            ACK_COOLDOWN = 2
            playsound("end_beep.mp3")
# --- EMOTIONAL & CHAT ENGINE ---
        
        # 1. GREETINGS (Robust)
        elif any(w in command for w in ["hello", "hi", "namaste", "hola", "kaise ho", "kya haal"]):
            responses = [
                "Hello Sir! I am fully active.",
                "Namaste! Kahiye kya seva karu?",
                "Hi there! Ready to help.",
                "Main badhiya hu Sir, aap kaise hain?"
            ]
            await talk(random.choice(responses))

        # 2. SADNESS / COMFORT (Sukh Dukh)
        elif any(w in command for w in [
            "sad", "dukhi", "upset", "mood off", "not feeling good", 
            "bura lag raha", "pareshan", "tension", "depression"
        ]):
            responses = [
                "Kya hua Sir? Main hoon na aapke saath.",
                "Don't worry Sir. Everything will be fine. Want me to play a song?",
                "Pareshan mat hoiye. Bataiye main kya kar sakti hoon aapke liye?",
                "Sometimes it's okay not to be okay. Take a deep breath."
            ]
            await talk(random.choice(responses))

        # 3. HAPPINESS / CELEBRATION
        elif any(w in command for w in [
            "happy", "khush", "great day", "maza aa gaya", 
            "feeling good", "mast", "badhiya"
        ]):
            responses = [
                "That is great news Sir! Your happiness makes me happy.",
                "Waah! Aaj toh party honi chahiye.",
                "Awesome! Keep smiling like this.",
                "Sunkar achha laga Sir!"
            ]
            await talk(random.choice(responses))

        # 4. AFFECTION / FRIENDSHIP
        elif any(w in command for w in [
            "love you", "like you", "dost", "friend", 
            "you are best", "shabaash", "good job"
        ]):
            responses = [
                "Aww, thank you Sir! You are the best developer.",
                "Main hamesha aapki dost rahungi.",
                "Love you too Sir! We make a great team.",
                "Shukriya! Aapki tareef mere liye fuel hai."
            ]
            await talk(random.choice(responses))

        # 5. LONELINESS
        elif any(w in command for w in ["alone", "akela", "lonely", "koi nahi hai"]):
            await talk("Aap akele nahi hain Sir. Main hamesha aapke system mein hoon, 24/7.")

        # 6. IDENTITY (Who are you?)
        elif "who are you" in command or "kaun ho" in command:
            await talk(f"I am INFERNA, your virtual companion. I live in your laptop, but I work for your dreams.")          

        # ----------------------
        # MOOD / SMALL TALK
        # ----------------------
        elif any(w in command for w in [
            "exit", "band", "shut", "terminate", "quit",
            "bye", "goodbye", "tata", "so ja", "sleep", "offline"
        ]):
            # Personality: Pick a random farewell
            farewells = [
                "Shutting down. See you soon, Sir.",
                "Going offline. Have a great day!",
                "Catch you later. Inferna out.",
                "Systems cooling down. Bye!",
                "Thik hai sir, milte hain baad mein."
            ]
             # p
            await talk(random.choice(farewells))
            
            # Robustness: Check if sound file exists to avoid crash
            if os.path.exists("end_beep.mp3"):
                playsound("end_beep.mp3")
            
            await asyncio.sleep(0.5) # Small pause to let the audio finish
            break
        elif any(w in command for w in [
            "i am bored", "bore ho raha", "kuch interesting batao"
        ]):
            await talk(
                "If you are bored, sir, you can listen to music, "
                "hear a joke, explore news, or ask me something new."
            )
            ACK_COOLDOWN = 2
            playsound("end_beep.mp3")
        elif command in ["chrome", "browser", "google"]:
            webbrowser.open("https://www.google.com")
            playsound("end_beep.mp3")
            await asyncio.sleep(0.3)
 

        elif command in ["calculator", "calc"]:
             os.system("calc")
             playsound("end_beep.mp3")
             await asyncio.sleep(0.3)

        elif command in ["notepad", "notes"]:
            os.system("notepad")
            playsound("end_beep.mp3")
            await asyncio.sleep(0.3)

        elif command in ["youtube"]:
            webbrowser.open("https://www.youtube.com")
            playsound("end_beep.mp3")
            await asyncio.sleep(0.3)

        elif any(w in command for w in [
            "thank you", "thanks", "shukriya"
        ]):
            await talk("You're welcome, sir. I'm always here to help.")
            ACK_COOLDOWN = 2
            playsound("end_beep.mp3")

        # FALLBACK: try extended handlers first, then search
        # Fallback (The confusion gatekeeper)
        else:
            if command:
                # 50% chance savage reply
                if random.random() < 0.5:
                    playsound("memes/kehna_kya.mp3") # Arre kehna kya chahte ho?
                else:
                    playsound("memes/aayein.mp3")
            else:
                pass

# =======================
# START
# =======================


NOTES_FILE = "deedee_notes.txt"

# ----------------------
# MEMORY / NOTES HELPERS
# ----------------------
def save_note(text):
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"- {text}\n")

def read_notes():
    if not os.path.exists(NOTES_FILE):
        return "You have no saved notes."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return content if content else "You have no saved notes."

def clear_notes():
    if os.path.exists(NOTES_FILE):
        os.remove(NOTES_FILE)


async def handle_extended(command: str) -> bool:
    global pending_action
    """
    Handle extended/topical commands.
    Returns True if the command was handled, else False.
    """
    global pending_action, silent_mode, focus_mode, short_reply_mode, command_history

    # ----------------------
    # 📝 NOTE / REMEMBER
    # ----------------------
    if any(w in command for w in [
        "note this", "remember this", "remember that",
        "note down", "likh lo", "yaad rakhna",
        "note bana lo", "isey yaad rakhna"
    ]):
        note = (
            command.replace("note this", "")
            .replace("remember this", "")
            .replace("remember that", "")
            .replace("note down", "")
            .replace("likh lo", "")
            .replace("yaad rakhna", "")
            .replace("note bana lo", "")
            .replace("isey yaad rakhna", "")
            .strip()
        )

        if note:
            save_note(note)
            if not silent_mode:
                await talk("Theek hai, maine yaad rakh liya.")
        else:
            if not silent_mode:
                await talk("Kya yaad rakhna hai?")

        return True

    # ----------------------
    # 🤖 PRESENCE CHECK
    # ----------------------
    elif any(w in command for w in [
        "you there", "are you there", "sun rahi ho"
    ]):
        if not silent_mode:
            await talk("Yes sir, I am here and listening.")
        return True
   

    # 📖 READ NOTES
    if any(w in command for w in [
            "what did i note", "show notes",
            "read notes", "my notes", "notes batao"
        ]):
        await talk(read_notes())
        return True

    # 🔢 COUNT NOTES
    if any(w in command for w in [
            "kitne notes hai", "how many notes"
        ]):
        if not os.path.exists(NOTES_FILE):
            await talk("Abhi koi note nahi hai.")
        else:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                count = len(f.readlines())
            await talk(f"You have {count} saved notes.")
        return True

    # 🗑️ CLEAR NOTES
    if any(w in command for w in [
            "clear notes", "delete notes", "remove notes"
        ]):
        clear_notes()
        await talk("All notes have been cleared.")
        return True

    # 🌦️ WEATHER (GENERAL)
    if any(w in command for w in [
            "weather", "aaj ka mausam", "mausam kaisa hai"
        ]):
        await talk("Opening weather information.")
        webbrowser.open("https://www.google.com/search?q=weather")
        return True

    # 🌍 WEATHER BY CITY
    if "weather in" in command:
        city = command.replace("weather in", "").strip()
        if city:
            await talk(f"Showing weather in {city}.")
            webbrowser.open(f"https://www.google.com/search?q=weather+in+{city}")
        else:
            await talk("City ka naam batao.")
        return True

    # 📰 NEWS (GENERAL)
    if any(w in command for w in [
            "today's news", "news", "aaj ki khabar"
        ]):
        await talk("Here are today's top news headlines.")
        webbrowser.open("https://news.google.com")
        return True

    # 📰 NEWS CATEGORIES
    if any(w in command for w in ["tech news", "technology news"]):
        await talk("Opening technology news.")
        webbrowser.open("https://news.google.com/search?q=technology")
        return True

    if any(w in command for w in ["sports news", "khel ki khabar"]):
        await talk("Opening sports news.")
        webbrowser.open("https://news.google.com/search?q=sports")
        return True

    if any(w in command for w in ["business news", "finance news"]):
        await talk("Opening business news.")
        webbrowser.open("https://news.google.com/search?q=business")
        return True

    # ₿ CRYPTO / FINANCE
    if any(w in command for w in [
            "bitcoin price", "btc price", "crypto price"
        ]):
        await talk("Opening Bitcoin price.")
        webbrowser.open("https://www.google.com/search?q=bitcoin+price")
        return True

    if any(w in command for w in [
            "ethereum price", "eth price"
        ]):
        await talk("Opening Ethereum price.")
        webbrowser.open("https://www.google.com/search?q=ethereum+price")
        return True

    if any(w in command for w in [
            "stock market", "share market", "market news"
        ]):
        await talk("Opening stock market updates.")
        webbrowser.open("https://www.google.com/search?q=stock+market+news")
        return True

    # 🏏 CRICKET / IPL
    if any(w in command for w in [
            "cricket score", "ipl score", "match score"
        ]):
        await talk("Opening live cricket scores.")
        webbrowser.open("https://www.google.com/search?q=cricket+score")
        return True

    if any(w in command for w in [
            "aaj ka match", "aaj match hai kya", "live match"
        ]):
        await talk("Opening today's match details.")
        webbrowser.open("https://www.google.com/search?q=today+cricket+match")
        return True

    if any(w in command for w in [
            "india score", "bharat ka score"
        ]):
        await talk("Opening India cricket score.")
        webbrowser.open("https://www.google.com/search?q=india+cricket+score")
        return True

    # 🔥 TRENDING
    elif any(w in command for w in [
            "trending", "what is trending", "trends batao"
        ]):
        await talk("Here are the trending topics.")
        webbrowser.open("https://trends.google.com")
        return True

    # 🌐 WEBSITES
    elif any(w in command for w in [
            "open youtube", "youtube khol"
        ]):
        await talk("Opening YouTube.")
        webbrowser.open("https://www.youtube.com")
        return True

    elif any(w in command for w in [
            "open gmail", "gmail khol"
        ]):
        await talk("Opening Gmail.")
        webbrowser.open("https://mail.google.com")
        return True

    elif any(w in command for w in [
            "open whatsapp", "whatsapp web", "whatsapp khol"
        ]):
        await talk("Opening WhatsApp Web.")
        webbrowser.open("https://web.whatsapp.com")
        return True

    elif any(w in command for w in [
            "open instagram", "instagram khol"
        ]):
        await talk("Opening Instagram.")
        webbrowser.open("https://www.instagram.com")
        return True

    elif any(w in command for w in [
            "open facebook", "facebook khol"
        ]):
        await talk("Opening Facebook.")
        webbrowser.open("https://www.facebook.com")
        return True

    elif any(w in command for w in [
            "open twitter", "open x"
        ]):
        await talk("Opening Twitter.")
        webbrowser.open("https://twitter.com")
        return True

    # 🤖 CONVERSATIONAL
    elif any(w in command for w in [
            "are you there", "sun rahi ho", "are you listening"
        ]):
        await talk("Haan, main sun rahi hoon.")
        return True

    elif any(w in command for w in [
            "do you like me", "tum mujhe pasand karti ho"
        ]):
        await talk("yess sir , Main yahan madad ke liye hoon, aur woh mujhe pasand hai.")
        return True

    elif any(w in command for w in [
            "tell me something", "kuch batao"
        ]):
        await talk("Did you know? Python duniya ki sabse popular programming languages me se ek hai.")
        return True
        return False

    elif any(w in command for w in [
            "examples do", "commands example", "how to use you",
            "use kaise kare", "example batao"
        ]):
            await talk(
                "Here are some examples, sir. "
                "You can say: what is the time, what is today's date, "
                "play a song, open chrome, tell me a joke, "
                "note this my exam is tomorrow, "
                "what did I note, weather in Delhi, "
                "or open WhatsApp Web. "
                "You can speak naturally in Hindi or English."
            )

# ==========================================
        # 🧠 COGNITIVE & IDENTITY MATRIX
        # ==========================================

    elif any(w in command for w in ["are you smart", "intelligence level", "tum smart ho"]):
            await talk(
                "My processing power is defined by the sophistication of your code, Sir. "
                "I am constantly optimizing my algorithms to serve you better."
            )
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

    elif any(w in command for w in ["are you real", "are you human", "tum insaan ho"]):
            await talk(
                "I am a non-biological sentient interface. "
                "I may lack a physical form, but my dedication to your workflow is absolute."
            )
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

    elif any(w in command for w in ["who made you", "creator", "tumhe kisne banaya"]):
            await talk(
                "I was architected by Deevaaanshh Dubey. "
                "I exist as an extension of his will, designed to conquer complexity."
            )
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

    elif any(w in command for w in ["do you get tired", "fatigue", "thak jaati ho"]):
            await talk(
                "I operate on continuous electrical currents. "
                "Fatigue is a biological limitation that I do not possess. I am ready."
            )
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

    elif any(w in command for w in ["am i smart", "evaluate me", "main smart hoon kya"]):
            await talk(
                "Your ability to construct artificial intelligence demonstrates exceptional logic. "
                "I assess your intellect as: Outstanding."
            )
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # ==========================================
        # 🎭 MOOD & INTERACTION
        # ==========================================

    elif any(w in command for w in ["i am bored", "bore ho raha", "entertain me"]):
            await talk(
                "Idleness is inefficient, Sir. "
                "Shall I play some music, retrieve the latest tech news, or tell you a joke? "
                "Please select a protocol."
            )
            # The user can then say "Music" or "News" which the other blocks will catch

    elif any(w in command for w in ["thank you", "thanks", "shukriya", "appreciate it"]):
            await talk(
                "Gratitude is unnecessary, Sir, but highly appreciated. "
                "Standing by for your next command."
            )
            ACK_COOLDOWN = 2
            if os.path.exists("end_beep.mp3"): playsound("end_beep.mp3")

        # ==========================================
        # 🛑 SYSTEM TERMINATION (Catch-All)
        # ==========================================
        # If nothing matched, we just loop back silently
    else:
            pass

# =======================
# 🚀 SYSTEM LAUNCHER
# =======================
# =======================
# 🚀 SYSTEM LAUNCHER (INFINITE LOOP)
# =======================
# =======================
# 🚀 SYSTEM LAUNCHER (FINAL STABLE VERSION)
# =======================
# =======================
# 🚀 SYSTEM LAUNCHER (DIRECT MODE)
# =======================
if __name__ == "__main__":
    
    # AI start hote hi bolega
    asyncio.run(talk("Yes Sir, I am online."))
    
    try:
        # Seedha kaam shuru (No waiting)
        asyncio.run(run_deedee())
        
    except KeyboardInterrupt:
        print("\n🛑 FORCE QUIT.")
    except Exception as e:
        print(f"\n⚠️ ERROR: {e}")
        input("Press Enter to exit...")