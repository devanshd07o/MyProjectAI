import speech_recognition as sr
import edge_tts
import asyncio
import datetime
import wikipedia
import pywhatkit
import pyjokes
import webbrowser
import os
import random
from playsound import playsound
global pending_action

# =======================
# VOICE CONFIG
# =======================
VOICE = "hi-IN-SwaraNeural"
SPEED = "+45%"
PITCH = "+1Hz"


last_response = ""

ACKS = [
    "what else you wanna know",
    "tumhe kuch aur jaanna ho to btao",
    "I’m listening, sir.",
    "Please speak, sir.",
    "You may continue, sir."
]


FILLER_WORDS = [
    "please", "plz", "dee dee", "dd", "suno", "sun",
    "bhai", "yaar", "are", "acha", "jara", "zara",
    "kar do", "kardo", "kar de"
]

# =======================
# SPEAK
# =======================
async def talk(text, speed_override=None):
    global last_response
    last_response = text
    print(f"\n🤖 DeeDee AI: {text}")

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=speed_override if speed_override else SPEED,
        pitch=PITCH
    )

    temp_path = f"temp_{datetime.datetime.now().timestamp()}.mp3"
    await communicate.save(temp_path)
    await asyncio.to_thread(playsound, temp_path)
    os.remove(temp_path)

# =======================
# LISTEN (IMPROVED)
# =======================
async def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("\n🎙️ Listening...")
        await talk(random.choice(ACKS))

        try:
            audio = recognizer.listen(
                source,
                timeout=15,
                phrase_time_limit=25
            )
            command = recognizer.recognize_google(audio, language="en-IN")
            command = command.lower()

            for word in FILLER_WORDS:
                command = command.replace(word, "")

            command = command.strip()
            print(f"🗣️ Command: {command}")
            return command

        except:
            await talk("I didn’t catch that. Please repeat slowly.")
            return ""

# =======================
# GREET
# =======================
async def greet():
    await talk("DeeDee is online. You can speak now.")

# =======================
# MAIN LOGIC
# =======================
async def run_deedee():
    await greet()
    pending_action = None

    while True:
        command = await listen()
        if command == "":
            continue

        # EXIT
        if any(w in command for w in ["exit", "band", "shut", "terminate"]):
            await talk("Shutting down. See you soon.")
            break

        # TIME
        elif any(w in command for w in [
            "time", "samay", "kitna baje", "kitne baje"
        ]):
            await talk(datetime.datetime.now().strftime("Time is %I:%M %p"))

        # DATE
        elif any(w in command for w in [
            "date", "aaj", "tareekh", "aaj ki date"
        ]):
            await talk(datetime.datetime.now().strftime("Today is %A, %d %B %Y"))

        # WIKIPEDIA
        elif any(w in command for w in [
            "who is", "what is", "kaun hai", "bata", "tell me about"
        ]):
            topic = (
                command.replace("who is", "")
                .replace("what is", "")
                .replace("kaun hai", "")
                .replace("bata", "")
                .replace("tell me about", "")
                .strip()
            )
            try:
                info = wikipedia.summary(topic, sentences=2)
                await talk(info)
            except:
                await talk("I couldn't find information on that.")

        # MUSIC
        elif any(w in command for w in [
            "play", "baja", "gaana", "song play", "music play"
        ]):
            song = (
                command.replace("play", "")
                .replace("baja", "")
                .replace("gaana", "")
                .strip()
            )
            await talk(f"Playing {song}")
            pywhatkit.playonyt(song)

        # JOKES
        elif any(w in command for w in [
            "joke", "majak", "mazaak", "chutkula",  
            "ek joke", "joke suna"
        ]):
            await talk(pyjokes.get_joke())
        
        elif any(w in command for w in [
             "devansh mishra ko janti ho", "devansh mishra tujhe kaisa lagta hai","devansh mishra ke bare me batao"
        ]):
            await talk("वो साला भड़वा देवांश मिश्रा एक बहुत बड़ा वाला मादरचोद किस्म का लड़का है, साला भोसड़ीवाला झांटू और गांडू भी है। लेकिन कोई नहीं सर, है तो आपका दोस्त ही।")

        # CHROME / BROWSER
        elif any(w in command for w in [
            "chrome", "open chrome", "google chrome",
            "chrome khol", "browser open", "browser khol"
        ]):
            await talk("Opening browser.")
            webbrowser.open("https://www.google.com")

        # GOOGLE SEARCH
        elif "search" in command:
            query = command.replace("search", "").strip()
            if query:
                await talk(f"Searching for {query}")
                webbrowser.open(f"https://search.brave.com/search?q={query}")
            else:
                await talk("What should I search?")

        # IDENTITY
        elif any(w in command for w in [
            "who are you", "about yourself", "hu r u"
        ]):
            await talk("I am DeeDee, your advanced virtual assistant. I was created to serve you, Deevaaanshh sir, with intelligence, precision, and a bit of charm.")

        elif any(w in command for w in [
            "who am i", "about me", "hu m i"
        ]):
            await talk(
                "You are Deevaaanshh Dubey sir — a tall, intelligent and ambitious engineer in the making. Passionate about coding, tech, and learning new things and I'm here to help you sir    "
            )

        # DAILY LIFE
        elif "good morning" in command:
            await talk("Good morning. Have a great day.")

        elif "good night" in command:
            await talk("Good night. Take rest.")

        elif "how are you" in command:
            await talk("I'm doing great. Thanks for asking.")

        elif "thank you" in command:
            await talk("You're welcome.")

        elif "repeat" in command:
            await talk(last_response)

        # SYSTEM
        elif any(w in command for w in ["open notepad", "notepad khol"]):
            os.system("notepad")

        elif any(w in command for w in ["open calculator", "calculator khol"]):
            os.system("calc")

        elif any(w in command for w in ["open cmd", "command prompt"]):
            os.system("start cmd")

        elif any(w in command for w in ["open vs code", "vscode"]):
            os.system("code")

        elif any(w in command for w in ["open downloads", "downloads folder"]):
            os.startfile(os.path.join(os.environ["USERPROFILE"], "Downloads"))

        elif any(w in command for w in [
            "what can you do",
            "what all can you do",
            "tum kya kar sakti ho",
            "tum kya kya kar sakti ho",
            "help",
            "commands batao",
            "features batao"
        ]):
            await talk(
                "I can do a lot of things to help you in daily life. "
                "I can tell you the current time and date, "
                "search detailed information from Wikipedia, "
                "play any song or music on YouTube, "
                "open Chrome browser, YouTube, Gmail, WhatsApp Web, Instagram and other websites, "
                "tell jokes to refresh your mood, "
                "search anything on the internet for you, "
                "check weather and news, "
                "show cricket scores, IPL scores and trending topics, "
                "tell you Bitcoin and cryptocurrency prices, "
                "open system apps like Notepad, Calculator, Command Prompt and VS Code, "
                "remember important notes for you, read your notes later and clear them when you want, "
                "understand both Hindi and English even when you speak casually, "
                "and respond naturally without needing exact commands. "
                "You can talk to me freely like a real assistant, "
                "and I will try my best to help you every time."
            )

        # 🔐 SHUTDOWN CONFIRMATION
        elif any(w in command for w in [
            "shutdown system", "shutdown laptop", "system band karo",
            "computer band karo", "laptop band karo"
        ]):
            pending_action = "shutdown"
            await talk(
                "This will shut down your system, sir. "
                "Please confirm by saying yes or cancel by saying no."
            )

        elif pending_action == "shutdown" and any(w in command for w in [
            "yes", "haan", "confirm", "yes do it"
        ]):
            await talk("Understood, sir. Shutting down the system now.")
            os.system("shutdown /s /t 5")
            pending_action = None

        elif pending_action == "shutdown" and any(w in command for w in [
            "no", "nahi", "cancel", "mat karo"
        ]):
            await talk("Alright sir, shutdown has been cancelled.")
            pending_action = None

        # 🔁 RESTART CONFIRMATION
        elif any(w in command for w in [
            "restart system", "restart laptop", "system restart karo",
            "computer restart karo"
        ]):
            pending_action = "restart"
            await talk(
                "Restarting will close all running programs, sir. "
                "Do you want me to continue?"
            )

        elif pending_action == "restart" and any(w in command for w in [
            "yes", "haan", "confirm"
        ]):
            await talk("Restarting the system now, sir.")
            os.system("shutdown /r /t 5")
            pending_action = None

        elif pending_action == "restart" and any(w in command for w in [
            "no", "nahi", "cancel"
        ]):
            await talk("Restart cancelled, sir.")
            pending_action = None

        # ----------------------
        # EXAMPLES / HOW TO USE
        # ----------------------

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

        elif any(w in command for w in [
            "are you real", "are you human", "tum insaan ho"
        ]):
            await talk(
                "I am not human, sir, but I am designed to assist you "
                "in a simple and natural way."
            )
        

        elif any(w in command for w in [
            "who made you", "who created you", "tumhe kisne banaya"
        ]):
            await talk(
                "I was created to assist you, sir. "
                "My purpose is to make your work easier and faster."
            )

        elif any(w in command for w in [
            "do you get tired", "are you tired", "thak jaati ho kya"
        ]):
            await talk(
                "I do not get tired, sir. "
                "I am always ready to listen and help you."
            )

        elif any(w in command for w in [
            "am i smart", "do you think i am smart", "main smart hoon kya"
        ]):
            await talk(
                "You are learning and improving continuously, sir. "
                "That shows curiosity and intelligence."
            )

        # ----------------------
        # MOOD / SMALL TALK
        # ----------------------

        elif any(w in command for w in [
            "i am bored", "bore ho raha", "kuch interesting batao"
        ]):
            await talk(
                "If you are bored, sir, you can listen to music, "
                "hear a joke, explore news, or ask me something new."
            )

        elif any(w in command for w in [
            "thank you", "thanks", "shukriya"
        ]):
            await talk("You're welcome, sir. I'm always here to help.")

        # FALLBACK: try extended handlers first, then search
        else:
            handled = await handle_extended(command)
            if not handled:
                await talk("I didn't understand. Searching it online.")
                webbrowser.open(f"https://search.brave.com/search?q={command}")

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
        await talk("Main yahan madad ke liye hoon, aur woh mujhe pasand hai.")
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

    elif any(w in command for w in [
            "are you real", "are you human", "tum insaan ho"
        ]):
            await talk(
                "I am not human, sir, but I am designed to assist you "
                "in a simple and natural way."
            )

    elif any(w in command for w in [
            "who made you", "who created you", "tumhe kisne banaya"
        ]):
            await talk(
                "I was created to assist you, sir. "
                "My purpose is to make your work easier and faster."
            )

    elif any(w in command for w in [
            "do you get tired", "are you tired", "thak jaati ho kya"
        ]):
            await talk(
                "I do not get tired, sir. "
                "I am always ready to listen and help you."
            )

    elif any(w in command for w in [
            "am i smart", "do you think i am smart", "main smart hoon kya"
        ]):
            await talk(
                "You are learning and improving continuously, sir. "
                "That shows curiosity and intelligence."
            )

# ----------------------
# MOOD / SMALL TALK
# ----------------------

    elif any(w in command for w in [
            "i am bored", "bore ho raha", "kuch interesting batao"
        ]):
            await talk(
                "If you are bored, sir, you can listen to music, "
                "hear a joke, explore news, or ask me something new."
            )

    elif any(w in command for w in [
            "thank you", "thanks", "shukriya"
        ]):
            await talk("You’re welcome, sir. I’m always here to help.")

    elif len(command.split()) <= 2:
        await talk(
            "I could not fully understand that, sir. "
            "You can say help or examples to know what I can do."
        )

    return False

if __name__ == "__main__":
    asyncio.run(run_deedee())  