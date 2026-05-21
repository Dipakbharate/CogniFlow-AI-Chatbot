from app.intent_detector import detect_intent, detect_intent_with_confidence
from app.image_gen import generate_image_url
from app.file_gen import generate_pdf, generate_docx
from app.config import GEMINI_API_KEY
from google import genai
from google.genai import types
import json
import re

class Chatbot:
    def __init__(self):
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            self.client = None

    def detect_intent_llm(self, message: str) -> str:
        if not self.client:
            return "general_query"
            
        prompt = f"""
        Analyze the following user query and categorize it into exactly one of these intents:
        - greeting (for hellos, introductions, standard welcomes, e.g. "hi", "hey there", "my name is Alice")
        - farewell (for goodbyes, signing off, ending conversations, e.g. "bye", "talk to you later")
        - image_request (for asking to generate, draw, paint, create, or display an image or picture, e.g. "generate an image of...", "draw a cat")
        - file_request (for asking to generate, export, save, or write a document, report, PDF, Word doc, or text file, e.g. "create a pdf report on...", "export this as docx")
        - contextual (for referring to previous statements, history, asking "what did I say earlier", "do you remember my name", "what is my preference", "what did we discuss yesterday")
        - general_query (for any general questions, explanations, coding, logic, or conversational queries that don't fit the above)

        User query: "{message}"

        Respond with ONLY the intent name (one of: greeting, farewell, image_request, file_request, contextual, general_query) in lowercase. No markdown, no quotes, no extra words.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            intent = response.text.strip().lower()
            intent = re.sub(r'[^a-z_]', '', intent)
            valid_intents = ["greeting", "farewell", "image_request", "file_request", "contextual", "general_query"]
            if intent in valid_intents:
                return intent
            return "general_query"
        except Exception as e:
            print(f"Error in LLM intent detection: {e}")
            return "general_query"

    def learn_preferences(self, message: str, current_prefs: dict) -> dict:
        if not self.client:
            return current_prefs
            
        prompt = f"""
        You are a personalization engine. Analyze the user's message to extract or update the user's long-term preferences.
        
        Current preferences: {json.dumps(current_prefs)}
        User Message: "{message}"
        
        Extract any stated or strongly implied preferences (e.g., preferred programming language, coding/documentation format, tone of voice, interests, response length).
        Update the preferences JSON object accordingly. If a preference has changed, overwrite the previous value. If no new preferences are found, return the current preferences object.
        
        Only return a valid JSON object representing the updated preferences.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            new_prefs = json.loads(response.text.strip())
            if isinstance(new_prefs, dict):
                return new_prefs
            return current_prefs
        except Exception as e:
            print(f"Error learning preferences: {e}")
            return current_prefs

    def extract_facts(self, message: str, current_facts: dict) -> dict:
        if not self.client:
            return current_facts
            
        prompt = f"""
        Analyze the user's message to extract or update key user facts.
        Current facts: {json.dumps(current_facts)}
        User Message: "{message}"
        
        We track the following keys:
        - "name": The user's name. Only set or update this if the user introduces themselves or states their name (e.g. "I am Dave", "My name is John", "call me Sarah").
        - "preferences": A summary string of general preferences or interests stated.
        - "last_topic": A short phrase representing the main topic/subject of the user's current message (e.g. "quantum computing", "react development", "greeting").
        
        Update the facts object. Only return a valid JSON object with these keys: "name", "preferences", "last_topic".
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            new_facts = json.loads(response.text.strip())
            updated_facts = current_facts.copy()
            for key in ["name", "preferences", "last_topic"]:
                if key in new_facts and new_facts[key] not in [None, "", "unknown", "none noted"]:
                    updated_facts[key] = new_facts[key]
            return updated_facts
        except Exception as e:
            print(f"Error extracting facts: {e}")
            return current_facts

    def _build_context_prompt(self, message: str, history: list, user_prefs: dict = None, facts: dict = None, last_session_history: list = None) -> str:
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
            
        if last_session_history:
            prompt += "\n--- Previous Session Conversation History ---\n"
            for msg in last_session_history[-5:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                if isinstance(content, dict):
                    content = content.get("content", "")
                prompt += f"{role}: {content}\n"
            prompt += "--- End of Previous Session Conversation History ---\n\n"

        if history:
            prompt += "Conversation history:\n"
            # Include the last 8 relevant messages for memory
            for msg in history[-8:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                if isinstance(content, dict):
                    content = content.get("content", "")
                prompt += f"{role}: {content}\n"
        prompt += f"\nUser's current query: {message}\nPlease respond accordingly."
        return prompt

    def process_message(self, message: str, history: list = None, user_prefs: dict = None, facts: dict = None, file_format: str = "pdf", last_session_history: list = None) -> dict:
        # 1. Detect intent with local classifier
        intent_res = detect_intent_with_confidence(message)
        intent = intent_res["intent"]
        confidence = intent_res["confidence"]
        
        # 2. Fall back to LLM-based intent detector if confidence is low
        source = "Local Classifier"
        if confidence < 0.75 and self.client:
            llm_intent = self.detect_intent_llm(message)
            print(f"[INTENT DETECTION] Classifier confidence ({confidence:.2%}) was low for '{message}'. LLM routing fallback: {llm_intent}")
            intent = llm_intent
            source = "LLM Fallback"
            
        intent_details = {
            "intent": intent,
            "confidence": confidence,
            "source": source,
            "local_intent": intent_res["intent"],
            "local_confidence": intent_res["confidence"],
            "scores": intent_res["scores"]
        }
        
        response_dict = {}
        if intent == "image_request":
            url = generate_image_url(message)
            response_dict = {
                "type": "image",
                "content": f"Here is your generated image:",
                "url": url
            }
            
        elif intent == "file_request":
            content = f"Generated content for request: {message}"
            if self.client:
                try:
                    prompt = self._build_context_prompt(message, history, user_prefs, facts, last_session_history)
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash', 
                        contents=f"Write content for a document based on this context and request:\n{prompt}"
                    )
                    content = response.text
                except Exception as e:
                    print(f"Error generating content: {e}")
            
            if file_format.lower() == "docx":
                filename = "generated_document.docx"
                filepath = generate_docx(content, filename)
                response_dict = {
                    "type": "file",
                    "content": "I have generated a DOCX file for you.",
                    "filepath": filepath,
                    "filename": filename
                }
            else:
                filename = "generated_document.pdf"
                filepath = generate_pdf(content, filename)
                response_dict = {
                    "type": "file",
                    "content": "I have generated a PDF file for you.",
                    "filepath": filepath,
                    "filename": filename
                }
            
        elif intent == "greeting":
            response_dict = {
                "type": "text",
                "content": "Hello! How can I help you today?"
            }
            
        elif intent == "farewell":
            response_dict = {
                "type": "text",
                "content": "Goodbye! Have a great day!"
            }
            
        elif intent in ["contextual", "general_query"]:
            response_text = "I'm sorry, please set your GEMINI_API_KEY in the .env file to process context."
            if self.client:
                try:
                    prompt = self._build_context_prompt(message, history, user_prefs, facts, last_session_history)
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash', 
                        contents=prompt
                    )
                    response_text = response.text
                    # Strictly gate images: Strip markdown images to prevent prompt leakage
                    response_text = re.sub(r'!\[.*?\]\(.*?\)', '[Image redacted: Please ask explicitly to generate images]', response_text)
                except Exception as e:
                    response_text = f"An error occurred: {e}"
            response_dict = {
                "type": "text",
                "content": response_text
            }
            
        else:
            response_dict = {
                "type": "text",
                "content": "I didn't quite catch that."
            }

        response_dict["intent_details"] = intent_details
        return response_dict

