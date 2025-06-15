import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os
import requests
from pynput import keyboard
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SpeechProcessor:
    def __init__(self):
        self.client = OpenAI()
        self.sample_rate = 44100
        self.channels = 1
        self.space_pressed = False

    def reset_space_pressed(self):
        """Reset the space_pressed flag to False."""
        self.space_pressed = False

    def on_press(self, key):
        if key == keyboard.Key.space:
            self.space_pressed = True
            return False  # Stop listener

    def record_audio_until_spacebar(self):
        """Record audio from microphone until the user presses the spacebar."""
        self.reset_space_pressed()  # Reset the flag before starting new recording
        print("Press the spacebar when you finish speaking.")
        recording = []
        blocksize = 1024
        dtype = 'float32'
        stream = sd.InputStream(samplerate=self.sample_rate, channels=self.channels, blocksize=blocksize, dtype=dtype)
        stream.start()
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        try:
            while not self.space_pressed:
                block, _ = stream.read(blocksize)
                recording.append(block)
        finally:
            stream.stop()
            stream.close()
            listener.stop()
            
        if not recording:
            raise ValueError("No audio was recorded. Please try again and make sure your microphone is working.")
            
        audio = np.concatenate(recording, axis=0)
        return audio

    def save_audio(self, recording, filename):
        """Save audio to a temporary file."""
        sf.write(filename, recording, self.sample_rate)

    def transcribe_audio(self, audio_file):
        """Transcribe audio using OpenAI's Whisper model."""
        with open(audio_file, "rb") as file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=file
            )
        return transcript.text

    def text_to_speech(self, text):
        """Convert text to speech using GPT-4o mini."""
        try:
            # Create speech using GPT-4o mini
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # You can choose from: alloy, echo, fable, onyx, nova, shimmer
                input=text
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file.flush()
                
                # Play the audio
                data, samplerate = sf.read(temp_file.name)
                sd.play(data, samplerate)
                sd.wait()
                
            # Clean up
            os.unlink(temp_file.name)
            
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
            # Fallback to printing the text if TTS fails
            print(f"Text (TTS failed): {text}")

    def process_speech_input(self):
        """Record and transcribe user's speech until spacebar is pressed."""
        # Record audio
        recording = self.record_audio_until_spacebar()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            self.save_audio(recording, temp_file.name)
            
            # Transcribe
            transcript = self.transcribe_audio(temp_file.name)
            
        # Clean up
        os.unlink(temp_file.name)
        return transcript

    def speak_response(self, text):
        """Convert agent's response to speech."""
        self.text_to_speech(text) 