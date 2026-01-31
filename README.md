# Nimbus – Spoken Dialogue System (Weather & Calendar)

Nimbus is a spoken dialogue system developed for an academic assignment.
It supports weather queries and calendar management using Automatic Speech Recognition (ASR) and rule-based Natural Language Understanding (NLU).

Due to hardware access limitations in Docker environments, Nimbus supports audio-file-based ASR inside Docker, as suggested by the course instructor.

---

## Features

### Weather
- Weather for today, tomorrow, and specific weekdays
- Multi-day forecasts (e.g. “next three days”)
- Context handling (e.g. “there” refers to the last mentioned city)
- Yes/No questions (rain, snow, mist, etc.)

### Calendar
- Add appointments with title, date, and time
- Query the next appointment
- Update appointment location
- Delete the previously created appointment
- Delete appointments by title
- Human-readable calendar responses

### Interaction Modes
- Type mode – text input
- Speak mode – live microphone ASR
- File mode – ASR using prerecorded audio files

---

## Project Structure

```
Nimbus/

├── api/
│   ├── weather.py
│   └── calendar.py
├── asr/
│   ├── recognize.py
│   └── recognize_file.py
├── tts/
│   └── speak.py
├── utils/
│   ├── intent.py
│   ├── weather_handler.py
│   ├── calendar_handler.py
│   └── setup_model.py
├── samples/
├── models/
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```
---

## Supported Commands

### Weather Commands
- What will the weather be like today in Marburg
- What will the weather be on Friday in Frankfurt
- Will it rain there on Saturday
- Will it snow there tomorrow
- Next three days in Hamburg

### Calendar Commands
- Add an appointment titled party for tomorrow at ten pm
- Where is my next appointment
- Change the place for my appointment tomorrow to Room twelve
- Delete the previously created appointment
- Delete appointment party

Contextual references such as there and previously created are resolved automatically.

---

## Audio File ASR (Docker-Compatible)

Docker containers cannot reliably access microphones or speakers due to hardware isolation.
Nimbus therefore supports speech input via prerecorded audio files when running inside Docker.

This ensures:
- Stable execution
- Reproducible demonstrations
- No dependency on host audio hardware

---

## File Mode (Recommended for Docker)

When running Nimbus, select File mode:

```
Modes: [T]ype, [S]peak, [F]ile, [Q]uit
```
In File mode, a numbered menu of prerecorded commands is shown.
The user selects a number to execute the corresponding audio command.
A custom audio file path can also be provided.

---

## Audio Format Requirements

All audio files must be:
- WAV format
- Mono channel
- 16-bit PCM
- 16 kHz sample rate

Example conversion using FFmpeg:
```
ffmpeg -i input.m4a -ac 1 -ar 16000 -sample_fmt s16 output.wav
```
---

## Docker Usage

Build the Docker image:
```
docker build -t nimbus .
```
Optional: download the ASR model during build:
```
docker build --build-arg DOWNLOAD_MODEL=true -t nimbus .
```
Run Nimbus with demo audio files:
```
docker run -it --rm -v "$(pwd)/samples:/app/samples" nimbus
```
---

## Deterministic Time for Demonstration

To avoid system clock inconsistencies, Nimbus supports a fixed reference time.

Run Docker with:
```
docker run -it --rm -e NIMBUS_NOW="2025-01-07 12:00" nimbus
```
This ensures that references such as today, tomorrow, and weekdays behave consistently during evaluation.

---

## Implementation Notes

- ASR implemented using Vosk
- NLU implemented using rule-based parsing
- Calendar intent resolution prioritizes specific commands over general ones
- Human-readable responses replace raw timestamps
- Dialogue context is maintained across turns

---

## Known Limitations

- Live microphone ASR is not supported inside Docker
- Calendar descriptions are optional and not parsed
- Time parsing relies on spoken number normalization (e.g. “ten p m”)

---

## Conclusion

Nimbus demonstrates a robust spoken dialogue system with:
- Multi-turn context handling
- Weather and calendar domain integration
- Docker-compatible ASR via audio files
- Clean and modular architecture