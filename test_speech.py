from speech_tools import SpeechProcessor

def main():
    processor = SpeechProcessor()
    
    print("Welcome to the Speech Tools Demo!")
    print("1. First, you'll be prompted to speak. Press spacebar when done.")
    print("2. Your speech will be transcribed and played back.")
    
    try:
        # Record and transcribe speech
        transcript = processor.process_speech_input()
        print(f"\nTranscribed text: {transcript}")
        
        # Convert transcript back to speech
        print("\nPlaying back the transcribed text...")
        processor.speak_response(transcript)
    except ValueError as e:
        print(f"\nError: {str(e)}")
        print("Please make sure your microphone is properly connected and try again.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        print("Please try again or check your system settings.")

if __name__ == "__main__":
    main() 