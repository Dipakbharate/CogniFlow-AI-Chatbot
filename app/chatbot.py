from app.intent_detector import detect_intent
from app.image_gen import generate_image_url
from app.file_gen import generate_pdf, generate_docx
from app.config import GEMINI_API_KEY
from google import genai
import json
import re

class Chatbot:
    def __init__(self):
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            self.client = None

    def learn_preferences(self, message: str, current_prefs: dict) -> dict:
        if not self.client:
            return current_prefs
            
        prompt = f"""
        Analyze the user's message and extract any explicitly stated or strongly implied preferences.
        Current preferences: {json.dumps(current_prefs)}
        User Message: "{message}"
        
        Update the preferences based on the message. Only return a valid JSON object. 
        If there are no new preferences, return the current preferences as JSON. 
        Do not include markdown blocks like ```json. Just the JSON text.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            new_prefs = json.loads(text.strip())
            return new_prefs
        except Exception as e:
            print(f"Error learning preferences: {e}")
            return current_prefs

    def _build_context_prompt(self, message: str, history: list, user_prefs: dict = None, facts: dict = None) -> str:
        memory_context = ""
        if facts:
            memory_context = f"""
You already know this about the user from previous sessions:
- Name: {facts.get('name', 'unknown')}
- Preferences: {facts.get('preferences', 'none noted')}
- Last topic discussed: {facts.get('last_topic', 'none')}

(Note: 'Last topic discussed' is from a previous interaction. Only mention it if it's directly relevant to the user's current query.)
"""
        prompt = f"{memory_context}\nYou are a helpful and personalized AI assistant.\n"
        if user_prefs:
            prompt += f"User Profile & Preferences: {json.dumps(user_prefs)}\n"
            prompt += "Please adapt your response, recommendations, and style to align with these preferences. DO NOT generate markdown images or external URLs in your response. If the user wants an image, they will ask explicitly.\n"
            
        if history:
            prompt += "Conversation history:\n"
            # Include the last 5 relevant messages for memory
            for msg in history[-5:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                if isinstance(content, dict):
                    content = content.get("content", "")
                prompt += f"{role}: {content}\n"
        prompt += f"\nUser's current query: {message}\nPlease respond accordingly."
        return prompt

    def process_message(self, message: str, history: list = None, user_prefs: dict = None, facts: dict = None, file_format: str = "pdf") -> dict:
        intent = detect_intent(message)
        
        if intent == "image_request":
            url = generate_image_url(message)
            return {
                "type": "image",
                "content": f"Here is your generated image:",
                "url": url
            }
            
        elif intent == "file_request":
            content = f"Generated content for request: {message}"
            if self.client:
                try:
                    prompt = self._build_context_prompt(message, history, user_prefs, facts)
                    response = self.client.models.generate_content(
                        model='gemini-3.1-flash-lite', 
                        contents=f"Write content for a document based on this context and request:\n{prompt}"
                    )
                    content = response.text
                except Exception as e:
                    print(f"Error generating content: {e}")
            
            if file_format.lower() == "docx":
                filename = "generated_document.docx"
                filepath = generate_docx(content, filename)
                return {
                    "type": "file",
                    "content": "I have generated a DOCX file for you.",
                    "filepath": filepath,
                    "filename": filename
                }
            else:
                filename = "generated_document.pdf"
                filepath = generate_pdf(content, filename)
                return {
                    "type": "file",
                    "content": "I have generated a PDF file for you.",
                    "filepath": filepath,
                    "filename": filename
                }
            
        elif intent == "greeting":
            return {
                "type": "text",
                "content": "Hello! How can I help you today?"
            }
            
        elif intent == "farewell":
            return {
                "type": "text",
                "content": "Goodbye! Have a great day!"
            }
            
        elif intent in ["contextual", "general_query"]:
            response_text = "I'm sorry, please set your GEMINI_API_KEY in the .env file to process context."
            if self.client:
                try:
                    prompt = self._build_context_prompt(message, history, user_prefs, facts)
                    response = self.client.models.generate_content(
                        model='gemini-3.1-flash-lite', 
                        contents=prompt
                    )
                    response_text = response.text
                    # Strictly gate images: Strip markdown images to prevent prompt leakage
                    response_text = re.sub(r'!\[.*?\]\(.*?\)', '[Image redacted: Please ask explicitly to generate images]', response_text)
                except Exception as e:
                    response_text = f"An error occurred: {e}"
            return {
                "type": "text",
                "content": response_text
            }
            
        else:
            return {
                "type": "text",
                "content": "I didn't quite catch that."
            }
