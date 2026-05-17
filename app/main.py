import streamlit as st
import uuid
import requests
import os

API_URL = "http://localhost:8001"

def main():
    st.set_page_config(page_title="CogniFlow AI", page_icon="🤖", layout="wide")
    st.title("🤖 CogniFlow AI")
    st.markdown("##### AI-Powered Personalized Multi-Session Chatbot with Intent Detection")
    
    # Initialize components
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'username' not in st.session_state:
        st.session_state.username = "default_user"
        
    # Sidebar User Profile
    st.sidebar.title("👤 User Profile")
    st.session_state.username = st.sidebar.text_input("Username", value=st.session_state.username)
    
    # Document Export Format Selection
    file_format = st.sidebar.selectbox("Document Export Format", ["PDF", "DOCX"], index=0)
    
    try:
        profile_res = requests.get(f"{API_URL}/profile/{st.session_state.username}").json()
        prefs = profile_res.get("preferences", {})
        if prefs:
            with st.sidebar.expander("Learned Preferences", expanded=False):
                st.json(prefs)
        else:
            st.sidebar.caption("No preferences learned yet.")
    except Exception as e:
        pass

    st.sidebar.divider()
        
    # Sidebar for Chat History
    st.sidebar.title("💬 Chat History")
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
        
    st.sidebar.divider()
    
    try:
        sessions_res = requests.get(f"{API_URL}/sessions/{st.session_state.username}").json()
        sessions = sessions_res.get("sessions", [])
        
        for s in sessions:
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                if st.button(s["title"], key=f"btn_{s['session_id']}", use_container_width=True):
                    st.session_state.session_id = s["session_id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{s['session_id']}"):
                    requests.delete(f"{API_URL}/history/{s['session_id']}")
                    if st.session_state.session_id == s["session_id"]:
                        st.session_state.session_id = str(uuid.uuid4())
                    st.rerun()
    except Exception as e:
        st.sidebar.warning("Could not load sessions.")
        
    # Load chat history from FastAPI Backend
    try:
        res = requests.get(f"{API_URL}/history/{st.session_state.session_id}")
        history = res.json().get("history", [])
    except Exception as e:
        history = []
        st.warning("⚠️ Could not connect to the FastAPI backend. Make sure to run: uvicorn app.api:app --reload")

    # Display chat history
    if not history:
        with st.chat_message("assistant"):
            st.write("👋 Welcome to CogniFlow AI! I can help you with:")
            st.write("- 🖼️ **Image Generation**")
            st.write("- 📄 **Document Generation**")
            st.write("- 🧠 **Contextual Chat**")
            st.write("How can I help you today?")
    else:
        for msg in history:
            with st.chat_message(msg["role"]):
                content = msg["content"]
                if isinstance(content, dict):
                    if content.get("type") == "image":
                        st.write(content.get("content"))
                        st.image(content.get("url"))
                    elif content.get("type") == "file":
                        st.write(content.get("content"))
                        filepath = content.get("filepath", "")
                        if os.path.exists(filepath):
                            with open(filepath, "rb") as f:
                                st.download_button(label="Download File", data=f, file_name=content.get("filename"), key=str(uuid.uuid4()))
                        else:
                            st.write("File no longer available on server.")
                    else:
                        st.write(content.get("content"))
                else:
                    st.write(content)

    # Chat input
    if prompt := st.chat_input("How can I help you today?"):
        # Display user message
        st.chat_message("user").write(prompt)
        
        # Get bot response via API
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_URL}/chat", json={
                    "session_id": st.session_state.session_id, 
                    "message": prompt,
                    "username": st.session_state.username,
                    "file_format": file_format.lower()
                }).json()
                
                with st.chat_message("assistant"):
                    if response.get("type") == "image":
                        st.write(response["content"])
                        st.image(response["url"])
                    elif response.get("type") == "file":
                        st.write(response["content"])
                        filepath = response.get("filepath", "")
                        if os.path.exists(filepath):
                            with open(filepath, "rb") as f:
                                st.download_button(label="Download File", data=f, file_name=response.get("filename"), key=str(uuid.uuid4()))
                    else:
                        st.write(response.get("content"))
            except Exception as e:
                st.error("Error communicating with the backend API. Is FastAPI running?")

if __name__ == "__main__":
    main()
