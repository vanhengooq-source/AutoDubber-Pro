import os
import sys
import time
import subprocess

os.system("cls")

print("[+] Checking Ngrok requirements...")
try:
    import pyngrok
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
from pyngrok import ngrok

print("==================================================")
print(" STARTING AUTODUBBER PRO (PERMANENT LINK)...")
print("==================================================")

# ខ្ញុំបានបញ្ចូល Token និង Domain របស់បងរួចរាល់
NGROK_TOKEN = "3IlZfOhAyylk88JnbZjNk1n3aRs_6sk4tcmwfXFbhg7ST347B" 
NGROK_DOMAIN = "prognosis-cameo-cloud.ngrok-free.dev"

print("\n1. Starting Web App in a NEW WINDOW...")
# ⚠️ បានតម្លើងទំហំ maxUploadSize ពី 500 ទៅ 2000 (2GB) ដើម្បីទទួលវីដេអូច្រើនបាន
os.system('start cmd /k "python -m streamlit run web_app.py --server.port 8585 --server.address 0.0.0.0 --server.enableCORS false --server.maxUploadSize 2000"')

print("⏳ Waiting 10 seconds for the app to load...")
time.sleep(10)

print("\n2. Connecting to Ngrok...")
try:
    ngrok.set_auth_token(NGROK_TOKEN)
    public_url = ngrok.connect(8585, domain=NGROK_DOMAIN).public_url
    
    print("\n" + "★"*55)
    print(f"🎉 ជោគជ័យ! លីងអចិន្ត្រៃយ៍របស់បងគឺ៖ {public_url}")
    print("-> លេខសម្ងាត់គឺ៖ 12345")
    print("⚠️ ហាមខ្វែងបិទផ្ទាំងនេះឱ្យសោះ ពេលកំពុងប្រើ។")
    print("★"*55 + "\n")
    
    ngrok_process = ngrok.get_ngrok_process()
    ngrok_process.proc.wait()
except Exception as e:
    print(f"\n❌ Error: {e}")