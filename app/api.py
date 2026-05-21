from fastapi import FastAPI
from pydantic import BaseModel
from app.chatbot import Chatbot
from app.memory import SQLiteMemory
from app.intent_detector import detect_intent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = Chatbot()
memory = SQLiteMemory()

class ChatRequest(BaseModel):
    session_id: str
    message: str
    username: str = "default_user"
    file_format: str = "pdf"

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    # Fetch history
    history = memory.get_history(request.session_id)
    
    # Fetch user preferences
    user_prefs = memory.get_user_preferences(request.username)
    
    # Learn and update preferences
    updated_prefs = bot.learn_preferences(request.message, user_prefs)
    if updated_prefs != user_prefs:
        memory.update_user_preferences(request.username, updated_prefs)
    
    # Update memory with user message
    memory.update_history(request.session_id, "user", request.message, request.username)
    
    # Fetch existing facts
    facts = memory.get_user_facts(request.username)
    
    # Extract and save updated facts (using LLM)
    updated_facts = bot.extract_facts(request.message, facts)
    for key, val in updated_facts.items():
        if val != facts.get(key):
            memory.save_user_fact(request.username, key, val)
            
    # Load last session history if current history is empty/short OR the user query is classified as contextual
    last_session_history = []
    local_intent = detect_intent(request.message)
    if len(history) < 2 or local_intent == "contextual":
        last_session_history = memory.get_last_session_history(request.username, request.session_id)
    
    # Process the message
    response = bot.process_message(
        message=request.message,
        history=history,
        user_prefs=updated_prefs,
        facts=updated_facts,
        file_format=request.file_format,
        last_session_history=last_session_history
    )
    
    # Update memory with assistant response
    memory.update_history(request.session_id, "assistant", response, request.username)
    
    return response

@app.get("/history/{session_id}")
def get_history(session_id: str):
    return {"history": memory.get_history(session_id)}

@app.get("/sessions/{username}")
def get_sessions(username: str):
    return {"sessions": memory.get_all_sessions(username)}

@app.delete("/history/{session_id}")
def delete_history(session_id: str):
    memory.clear_history(session_id)
    return {"status": "success"}

@app.get("/profile/{username}")
def get_profile(username: str):
    return {"preferences": memory.get_user_preferences(username)}

