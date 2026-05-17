from fastapi import FastAPI
from pydantic import BaseModel
from app.chatbot import Chatbot
from app.memory import SQLiteMemory
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
    
    # Fetch facts
    facts = memory.get_user_facts(request.username)
    
    # Process the message
    response = bot.process_message(request.message, history, updated_prefs, facts, request.file_format)
    
    # Extract and save facts (as per requirement)
    user_input = request.message
    if "my name is" in user_input.lower():
        name = user_input.lower().split("my name is")[-1].strip()
        memory.save_user_fact(request.username, "name", name)
    memory.save_user_fact(request.username, "last_topic", user_input[:100])
    
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

