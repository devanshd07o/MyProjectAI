import os
import io
import zipfile
import urllib.request

# --- CONFIGURATION ---
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
EXTRACT_FILES = ["ffmpeg.exe", "ffprobe.exe"]

print("\n" + "="*50)
print("🛠️  FFMPEG AUTO-INSTALLER (Inferna Fixer)")
print("="*50)
print(f"⬇️  Downloading FFmpeg from: {FFMPEG_URL}")
print("    (Size is approx 80MB. Please wait...)")

try:
    # 1. Download Zip into Memory
    with urllib.request.urlopen(FFMPEG_URL) as response:
        zip_data = response.read()

    print("✅ Download Complete. Extracting Engine...")

    # 2. Extract only ffmpeg.exe and ffprobe.exe
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        # Find the path inside the zip (it's usually inside a 'bin' folder)
        for file_info in z.infolist():
            if file_info.filename.endswith("ffmpeg.exe"):
                # Read the file content
                source = z.open(file_info)
                target = open("ffmpeg.exe", "wb")
                target.write(source.read())
                source.close()
                target.close()
                print("   -> Extracted: ffmpeg.exe")

            elif file_info.filename.endswith("ffprobe.exe"):
                source = z.open(file_info)
                target = open("ffprobe.exe", "wb")
                target.write(source.read())
                source.close()
                target.close()
                print("   -> Extracted: ffprobe.exe")

    print("\n🎉 SUCCESS! FFmpeg engine installed.")
    print("👉 Ab tum 'setup_memes.py' chala sakte ho.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Tip: Agar ye fail hua, toh manual download karna padega.")