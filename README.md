# Nimbus – Voice & Text Assistant (Dockerized)

Nimbus is a lightweight command-line personal assistant written in Python. It supports text input by default and optional voice input/output. The project is fully Dockerized for easy setup and reproducibility.

## Features

- Text-based interaction (always available)
- Optional speech recognition (ASR) using Vosk
- Text-to-speech (TTS) using pyttsx3
- Weather information via external API
- Calendar interaction
- Docker support

## Project Structure

nimbus/
├── main.py
├── setup.py
├── requirements.txt
├── Dockerfile
├── api/
│ └── **init**.py
├── asr/
│ └── **init**.py
├── tts/
│ └── **init**.py
└── models/

## Requirements (Non-Docker)

- Python 3.10+
- PortAudio
- espeak / espeak-ng

Install system dependencies (Debian/Ubuntu):
sudo apt install portaudio19-dev espeak espeak-ng

Install Python dependencies:
pip install -r requirements.txt

Run:
python main.py

## Running with Docker

Build the image:
docker build -t nimbus .

Run (text mode):
docker run -it nimbus

## Voice Mode in Docker (Linux)

docker run -it \
 --device /dev/snd \
 -v $(pwd)/models:/app/models \
 nimbus

## ASR Model (Vosk)

Download the Vosk English model manually:
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip

Expected path:
models/vosk-model-en-us-0.22/

If the model is missing, Nimbus automatically falls back to text mode.

## Configuration

- DOWNLOAD_MODEL=false (default)
  Prevents downloading large ASR models during Docker build.

## Notes

- Voice input requires microphone access.
- Docker Desktop on Windows/macOS supports text mode only.
- Speech recognition works reliably on Linux with /dev/snd access.

## License

MIT License
