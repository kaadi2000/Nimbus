import sys
from tts.speak import TTSEngine

from utils.intent import detect_intent
from utils.nimbus_state import MODEL_PATH, context
from utils.weather_handler import handle_weather
from utils.calendar_handler import handle_calendar
import utils.setup_model as setup_model

def main() -> None:
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
        print("Modes: [T]ype, [S]peak, [Q]uit")
        mode = input("\nMode > ").strip().lower()
        if mode in ["q", "quit", "exit"]:
            break

        if mode == "s":
            if asr is None:
                print("❌ ASR isn't available. Use Type mode.")
                continue
            text = asr.listen_push_to_talk()
            print("📝 ASR heard:", text)
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
