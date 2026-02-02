import sys
from tts.speak import TTSEngine

from utils.intent import detect_intent
from utils.nimbus_state import MODEL_PATH, context
from utils.weather_handler import handle_weather
from utils.calendar_handler import handle_calendar
import utils.setup_model as setup_model
from asr.recognize_file import ASRFileEngine


DEMO_AUDIO_FILES = [
    ("What will the weather be like today in Marburg", "samples/01_What_will_the_weather_be_like_today_in_Marburg.wav"),
    ("What will the weather be on Friday in Frankfurt", "samples/02_What_will_the_weather_be_on_Friday_in_Frankfurt.wav"),
    ("Will it rain there on Saturday", "samples/03_Will_it_rain_there_on_Saturday.wav"),
    ("Will it snow there tomorrow", "samples/04_Will_it_snow_there_tomorrow.wav"),
    ("Next three days in Hamburg", "samples/05_Next_three_days_in_Hamburg.wav"),
    ("What will the weather be for the next three days in Munich", "samples/06_What_will_the_weather_be_for_the_next_three_days_in_Munich.wav"),
    ("Add an appointment titled party for tomorrow at ten pm", "samples/07_Add_an_appointment_titled_party_for_tomorrow_at_ten_pm.wav"),
    ("Where is my next appointment", "samples/08_Where_is_my_next_appointment.wav"),
    ("Change the place for my appointment tomorrow to Room twelve", "samples/09_Change_the_place_for_my_appointment_tomorrow_to_Room_twelve.wav"),
    ("Delete the previously created appointment", "samples/10_Delete_the_previously_created_appointment.wav"),
    ("Add an appointment titled team meeting for Friday at nine am", "samples/11_Add_an_appointment_titled_team_meeting_for_Friday_at_nine_am.wav"),
    ("Delete appointment titled team meeting", "samples/12_Delete_appointment_titled_team_meeting.wav")
]

def choose_demo_audio():
    print("\nSelect an audio command:\n")
    for i, (label, _) in enumerate(DEMO_AUDIO_FILES, start=1):
        print(f"{i}) {label}")

    choice = input("\nEnter number > ").strip()

    if not choice.isdigit():
        return None

    idx = int(choice)

    if 1 <= idx <= len(DEMO_AUDIO_FILES):
        return DEMO_AUDIO_FILES[idx - 1][1]

    if idx == len(DEMO_AUDIO_FILES) + 1:
        return input("Enter custom .wav file path > ").strip()

    return None

def main() -> None:
    file_asr = None
    try:
        file_asr = ASRFileEngine(model_path=MODEL_PATH)
    except Exception as e:
        print(f"File ASR not available ({e}).")
    
    tts = TTSEngine()

    asr = None
    check_asr = True

    while check_asr:
        try:
            from asr.recognize import ASREngine
            asr = ASREngine(model_path=MODEL_PATH)
            check_asr = False

        except Exception as e:
            choice = input(f"ASR not available ({e}). Type mode still works. Continue without ASR? [y/n]: ").strip().lower()
            if choice == "n":
                try:
                    setup_model.main()
                    check_asr = False
                except Exception as e:
                    print(f"\nFailed to set up model: {e}\n")
            else:
                check_asr = False


    print("Nimbus online.")

    while True:
        print("Modes: [T]ype, [S]peak, [F]ile, [Q]uit")
        mode = input("\nMode > ").strip().lower()
        if mode in ["q", "quit", "exit"]:
            break
        
        elif mode == "f":
            path = choose_demo_audio()
            if not path:
                print("Invalid selection.")
                continue

            try:
                text = file_asr.transcribe_wav(path)
            except Exception as e:
                reply = f"Could not transcribe audio: {e}"
                print("Bot:", reply)
                tts.say(reply)
                continue

            print(" ASR heard:", text)
            if not text:
                reply = "Sorry, I didn’t catch that in the audio."
                print("Bot:", reply)
                tts.say(reply)
                continue

        elif mode == "s":
            if asr is None:
                print(" ASR isn't available. Use Type mode.")
                continue
            text = asr.listen_push_to_talk()
            print(" ASR heard:", text)
            if not text:
                reply = "Sorry, I didn’t catch that. Please try again."
                print("Bot:", reply)
                tts.say(reply)
                continue
        elif mode == "t":
            text = input("You: ").strip()
        else:
            print("\nWhat are you trying to do? There is no mode for that.\n")
            continue

        if not text:
            continue

        intent = detect_intent(text)
        context["last_intent"] = intent

        if intent == "weather":
            reply = handle_weather(text)
        elif intent == "calendar":
            reply = handle_calendar(text)
        else:
            reply = "Try: 'weather Frankfurt tomorrow' or 'Where is my next appointment?'"

        print("Bot:", reply)
        tts.say(reply)


if __name__ == "__main__":
    main()
