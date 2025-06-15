# AI Therapist Agent

An AI-powered therapist agent that can engage in natural conversations using speech recognition and text-to-speech capabilities.

## Features

- Natural speech interaction using microphone input
- Realistic voice responses using OpenAI's GPT-4o mini TTS
- OpenAI GPT-4 powered responses
- Session history tracking
- Automatic session summarization
- Professional therapeutic approach

## Setup

1. Clone the repository:
```bash
git clone https://github.com/E10Feng/ShrinkAgent.git
cd ShrinkAgent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API key:
```
OPENAI_API_KEY=your_openai_api_key
```

## Usage

Run the agent:
```bash
python agent.py
```

The agent will:
1. Start listening for your voice input
2. Transcribe your speech to text
3. Process your input using GPT-4
4. Respond with a natural-sounding voice

To end the session, simply say "quit" or type "quit" when prompted.

## Dependencies

- OpenAI API (GPT-4, Whisper, and TTS)
- sounddevice (Audio recording)
- soundfile (Audio file handling)
- numpy and scipy (Audio processing)
- python-dotenv (Environment variables)

## Notes

- The agent uses a 5-second recording window by default for speech input
- The voice is set to "alloy" by default but can be changed to other options: echo, fable, onyx, nova, shimmer
- All sessions are automatically saved with timestamps
- The agent maintains conversation history for context

## License

MIT License 