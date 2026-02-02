import os
import sys
import requests
from tqdm import tqdm
import zipfile

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
MODEL_DIR = "models/vosk-model-en-us-0.22"
ZIP_PATH = "models/vosk-model-en-us-0.22.zip"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_model():
    ensure_dir("models")
    print(f" Model not found at '{MODEL_DIR}'.")
    print("Downloading Vosk model (1.8 GB)... this may take a while depending on your internet speed.\n")

    with requests.get(MODEL_URL, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(ZIP_PATH, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc="Downloading"
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
    print("\n Download complete.")

def extract_model():
    print(" Extracting model files...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall("models")
    print(" Extraction complete.")

    try:
        os.remove(ZIP_PATH)
        print(" Clean-up done — deleted downloaded zip file.")
    except Exception as e:
        print(f" Could not delete zip file. You can manually delete it at '{ZIP_PATH}': {e}")

def verify_model():
    return os.path.exists(os.path.join(MODEL_DIR, "am", "final.mdl"))

def main():
    print(" Checking for Vosk model...")
    if verify_model():
        print(f"Model found at '{MODEL_DIR}'.")
        return

    download_model()
    extract_model()

    if verify_model():
        print(f"\n Model setup successful! Ready to use at '{MODEL_DIR}'.")
    else:
        print("\n Something went wrong: model verification failed.")
        sys.exit(1)
