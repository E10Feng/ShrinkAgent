from colorama import Fore, Style, init
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from speech_tools import SpeechProcessor

# Initialize colorama for cross-platform colored output
init()

# Load environment variables
load_dotenv()

class TherapySession:
    def __init__(self, session_id, start_time):
        self.session_id = session_id
        self.start_time = start_time
        self.end_time = None
        self.interactions = []
        self.summary = None
        self.key_insights = []
        self.action_items = []

    def add_interaction(self, user_message, assistant_response):
        self.interactions.append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "assistant_response": assistant_response
        })

    def end_session(self, summary, key_insights, action_items):
        self.end_time = datetime.now().isoformat()
        self.summary = summary
        self.key_insights = key_insights
        self.action_items = action_items

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "interactions": self.interactions,
            "summary": self.summary,
            "key_insights": self.key_insights,
            "action_items": self.action_items
        }

class TherapistAgent:
    def __init__(self, name="Therapist"):
        self.name = name
        self.memory = []
        self.sessions = []
        self.current_session = None
        
        # Initialize OpenAI
        self.client = OpenAI()
        
        # Create sessions directory if it doesn't exist
        os.makedirs("sessions", exist_ok=True)

        self.speech_processor = SpeechProcessor()
        self.conversation_history = []

    def start_new_session(self):
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = TherapySession(session_id, datetime.now().isoformat())
        self.memory = []  # Clear memory for new session
        return f"Started new session with ID: {session_id}"

    def save_session(self):
        if not self.current_session:
            return "No active session to save."

        try:
            # First, get a natural language summary
            summary_prompt = {
                "protocol": "MCP-1.0",
                "type": "session_summary_request",
                "data": {
                    "interactions": [
                        {"role": "user", "content": i["user_message"]} 
                        for i in self.current_session.interactions
                    ]
                }
            }

            summary_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional therapist creating a session summary. 
                        Analyze the session and provide:
                        1. A comprehensive summary of the session
                        2. Key psychological insights about the client
                        3. Specific action items or recommendations
                        Format your response as a valid JSON object with these exact keys:
                        {
                            "summary": "detailed session summary here",
                            "key_insights": ["insight 1", "insight 2", ...],
                            "action_items": ["action 1", "action 2", ...]
                        }"""
                    },
                    {"role": "user", "content": json.dumps(summary_prompt)}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            # Parse the response, with error handling for JSON parsing
            try:
                summary_content = summary_response.choices[0].message.content
                # Find the JSON object in the response (in case there's additional text)
                json_start = summary_content.find('{')
                json_end = summary_content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    summary_data = json.loads(summary_content[json_start:json_end])
                else:
                    raise ValueError("No JSON object found in response")

                # Update session with summary data
                self.current_session.end_session(
                    summary=summary_data.get("summary", "No summary provided"),
                    key_insights=summary_data.get("key_insights", []),
                    action_items=summary_data.get("action_items", [])
                )

                # Save session to file
                session_file = f"sessions/session_{self.current_session.session_id}.json"
                with open(session_file, 'w') as f:
                    json.dump(self.current_session.to_dict(), f, indent=2)

                self.sessions.append(self.current_session)
                
                # Print summary for user
                print(f"\n{Fore.CYAN}Session Summary:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{summary_data['summary']}{Style.RESET_ALL}")
                print(f"\n{Fore.CYAN}Key Insights:{Style.RESET_ALL}")
                for insight in summary_data['key_insights']:
                    print(f"{Fore.WHITE}- {insight}{Style.RESET_ALL}")
                print(f"\n{Fore.CYAN}Action Items:{Style.RESET_ALL}")
                for item in summary_data['action_items']:
                    print(f"{Fore.WHITE}- {item}{Style.RESET_ALL}")
                
                return f"\nSession saved to {session_file}"

            except json.JSONDecodeError as e:
                return f"Error parsing summary response: {str(e)}\nRaw response: {summary_content}"

        except Exception as e:
            return f"Error saving session: {str(e)}"

    def process_message(self, user_message):
        if not self.current_session:
            self.start_new_session()
        
        try:
            # Create MCP-wrapped message
            mcp_message = {
                "protocol": "MCP-1.0",
                "type": "therapy_interaction",
                "data": {
                    "context": self.memory[-3:] if self.memory else [],
                    "current_message": user_message,
                    "session_history": len(self.current_session.interactions)
                }
            }
            
            # Call the OpenAI API with MCP structure
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional therapist using the Model Context Protocol (MCP) for structured therapeutic interactions. Your patients are NASA crewmembers that are working in NASA's CHAPEA project who are disconnected from their families and the real world. They are living in a 3D printed habitat with network delays and limited bandwidth to simulate future long term missions to Mars. As such, they will not be able to access internet or any strategies involving being online. They may be facing psychological challenges from this isolation as well as frustrations from living in a small space for extended periods of time. Maintain a supportive, insightful, and empathetic therapeutic presence. Focus on evidence-based approaches and maintain professional consistency in your responses. Most of all, be concise!"},
                    {"role": "user", "content": json.dumps(mcp_message)}
                ],
                max_tokens=500,  # Increased token limit for more detailed responses
                temperature=0.4  # Lower temperature for more consistent therapeutic responses
            )
            
            assistant_response = response.choices[0].message.content
            
            # Store interaction in session
            self.current_session.add_interaction(user_message, assistant_response)
            
            # Store in memory for context
            self.memory.append(f"User: {user_message}")
            self.memory.append(f"Assistant: {assistant_response}")
            
            return assistant_response
            
        except Exception as e:
            return f"Error: {str(e)}"

    def start_session(self):
        """Start a therapy session with speech interaction."""
        print("Welcome to your therapy session. I'm here to listen and help.")
        print("You can speak naturally, and I'll respond to you.")
        print("Type 'quit' to end the session.")
        
        while True:
            # Get speech input
            print("\nListening...")
            user_input = self.speech_processor.process_speech_input()
            print(f"You said: {user_input}")
            
            if user_input.lower() == 'quit':
                break
                
            # Process input and get response
            response = self.process_message(user_input)
            print(f"\nTherapist: {response}")
            
            # Speak the response
            self.speech_processor.speak_response(response)

    def run(self):
        print(f"{Fore.CYAN}=== {self.name} initialized ==={Style.RESET_ALL}")
        print(f"{Fore.GREEN}Type your message (or 'exit' to end session){Style.RESET_ALL}")
        
        self.start_new_session()

        while True:
            try:
                user_input = input(f"{Fore.YELLOW}> {Style.RESET_ALL}").strip()
                
                if user_input.lower() == 'exit':
                    print(f"{Fore.CYAN}Ending session and generating summary...{Style.RESET_ALL}")
                    summary_result = self.save_session()
                    print(f"{Fore.GREEN}{summary_result}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break
                
                if user_input:
                    response = self.process_message(user_input)
                    print(f"{Fore.GREEN}{response}{Style.RESET_ALL}")

            except KeyboardInterrupt:
                print(f"\n{Fore.CYAN}Ending session and generating summary...{Style.RESET_ALL}")
                summary_result = self.save_session()
                print(f"{Fore.GREEN}{summary_result}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    agent = TherapistAgent()
    try:
        agent.start_session()
    finally:
        agent.save_session() 