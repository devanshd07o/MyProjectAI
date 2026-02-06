import os
import yt_dlp

# --- 📂 FOLDER SETUP (Target: memes3) ---
TARGET_FOLDER = "memes3"
if not os.path.exists(TARGET_FOLDER):
    os.makedirs(TARGET_FOLDER)

# --- 🎵 MEME DATABASE (Wahi purani list) ---
MEME_MAP = {
    # --- 1. CONFUSION ---
    "aayein.mp3": "Aayein Baingan short sound effect",
    "kehna_kya.mp3": "Arre kehna kya chahte ho short sound",
    "kuch_bhi.mp3": "Kuch bhi Arnab Goswami sound effect",
    "samajh_rahe_ho.mp3": "Samajh rahe ho na Harmonium chacha short",
    "bhai_kya_dekh.mp3": "Bhai ye kya dekh liya sound effect",
    "kya_matlab.mp3": "Kya matlab main galat hoon sound",
    "mera_matlab.mp3": "Mera matlab kuch aur tha sound",

    # --- 2. SAD / PAIN ---
    "moye_moye.mp3": "Moye Moye short sound effect",
    "ye_dukh.mp3": "Ye dukh kaahe khatam nahi hota sound",
    "kyun_toda.mp3": "Mujhe kyun toda sound effect",
    "aadat.mp3": "Ab toh aadat si hai mujhko sound",
    "mar_jaata.mp3": "Isse achha toh main mar hi jaata sound",
    "galti_meri.mp3": "Galti meri hi thi meme sound",
    "safar_khatam.mp3": "Bas yahin tak tha mera safar sound",
    "acha_sila.mp3": "Acha sila diya tune mere pyaar ka sound",
    "loota.mp3": "Humko toh apno ne loota sound",
    "darr_lag_raha.mp3": "Ab toh sach me darr lag raha hai sound",

    # --- 3. ANGER / FRUSTRATION ---
    "maaro_mujhe.mp3": "Bhai maaro mujhe maaro short sound",
    "bas_kar.mp3": "Bas kar bhai sound effect",
    "rehne_de.mp3": "Bhai tu rehne de sound effect",
    "job_chhod.mp3": "Main kya karoon job chhod doon sound",
    "tumse_na.mp3": "Beta tumse na ho payega short sound",
    "pagal_bana_rahe.mp3": "Ye sab milke humko pagal bana rahe hain sound",
    "galat_hai.mp3": "Bhai ye toh galat hai sound",
    "fayda.mp3": "Isme mera kya fayda sound",
    "dushman.mp3": "Mera sabse bada dushman main khud hoon sound",

    # --- 4. SARCASM / INSULT ---
    "waah.mp3": "Waah Sampy Waah short sound",
    "krrish.mp3": "Krrish woo sound effect short",
    "wow.mp3": "So beautiful so elegant just looking like a wow short",
    "clapping.mp3": "Slow clapping sound effect",
    "aisa_kaun.mp3": "Aisa kaun karta hai bhai sound",
    "kis_line.mp3": "Bhai sahab ye kis line me aa gaye aap sound",
    "pehli_baar.mp3": "Pehli baar dekha hai kya sound",
    "hum_alag.mp3": "Hum alag hain meme sound",
    "civic_sense.mp3": "Civic sense meme sound",

    # --- 5. TECH / SYSTEM / REALITY ---
    "system_hang.mp3": "System hang ho gaya sound effect",
    "laga_kuch_aur.mp3": "Mujhe laga kuch aur hi hoga sound",
    "dhokha.mp3": "Padhai likhai dhokha hai sound",
    "expectation.mp3": "Expectation vs Reality sound effect",
    "moh_maya.mp3": "Ye sab moh maya hai sound",
    
    # --- 6. DELAY / STOP ---
    "ruko_zara.mp3": "Ruko zara sabar karo sound effect",
    "wait.mp3": "Wait a minute who are you sound",
    
    # --- 7. MOTIVATION / FLEX ---
    "toofani.mp3": "Aaj kuch toofani karte hain sound",
    "zindagi_ho.mp3": "Zindagi ho toh aisi ho sound",
    "hum_first.mp3": "Hum first hum first sound",
    "baat_sahi.mp3": "Baat toh sahi hai sound",
    "vishwas.mp3": "Pehle istemal karein phir vishwas karein sound",
    "maturity.mp3": "Kya matlab samajhdaar banna padega sound",
    "sab_theek.mp3": "Sab theek ho jaayega meme sound",
    
    # --- 8. TRENDING EXTRAS ---
    "chin_tapak.mp3": "Chin tapak dam dam short sound",
    "elvish.mp3": "Arre Elvish bhai short sound",
    "papa_nahi.mp3": "Papa nahi maanenge sound",
}

# --- 🧠 STRICT FILTER (< 7 Seconds) ---
def filter_duration(info, *, incomplete):
    """Reject anything longer than 7 seconds"""
    duration = info.get('duration')
    if duration and duration > 7:
        return 'Video too long'

# --- 🚀 DOWNLOADER LOGIC ---
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': f'{TARGET_FOLDER}/%(title)s.%(ext)s', # Output to memes3
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'no_warnings': True,
    'match_filter': filter_duration, # Strict Filter
    'noplaylist': True,
}

print(f"\n🔥 INFERNA DOWNLOADER: Targeting '{TARGET_FOLDER}' (Max 7s clips)")
print("="*50)

for filename, query in MEME_MAP.items():
    final_path = os.path.join(TARGET_FOLDER, filename)
    
    # Check agar memes3 mein pehle se hai
    if os.path.exists(final_path):
        print(f"✅ Exists in {TARGET_FOLDER}: {filename}")
        continue

    print(f"⬇️  Hunting: '{query}'...")
    
    try:
        # Search Top 20 results to find the perfect short clip
        search_query = f"ytsearch20:{query}" 
        
        current_opts = ydl_opts.copy()
        # Force filename inside memes3
        current_opts['outtmpl'] = f"{TARGET_FOLDER}/{filename.replace('.mp3', '')}"
        
        with yt_dlp.YoutubeDL(current_opts) as ydl:
            ydl.download([search_query])
            
        # Verify
        if os.path.exists(final_path):
            print(f"🎉 Saved to {TARGET_FOLDER}: {filename}")
        else:
            print(f"⚠️ Could not find a <7s clip for: {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n✨ All operations complete! Check the 'memes3' folder.")