import streamlit as st
import uuid
import requests
import os
from textwrap import dedent

API_URL = "http://localhost:8001"

def render_intent_details(intent_details: dict):
    if not intent_details:
        return
        
    intent = intent_details.get("intent", "unknown")
    source = intent_details.get("source", "unknown")
    local_intent = intent_details.get("local_intent", "")
    local_confidence = intent_details.get("local_confidence", 0.0)
    scores = intent_details.get("scores", {})
    
    # Format intent label
    intent_display = intent.replace("_", " ").title()
    
    # Build breakdown HTML
    breakdown_html = ""
    for lbl, prob in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar_width = f"{prob * 100:.1f}%"
        is_selected = (lbl == intent)
        lbl_display = lbl.replace("_", " ").title()
        color = "#00e5ff" if is_selected else "inherit"
        weight = "600" if is_selected else "normal"
        opacity = "1" if is_selected else "0.75"
        bar_color = "linear-gradient(90deg, #00e5ff, #00ff87)" if is_selected else "rgba(128, 128, 128, 0.3)"
        
        breakdown_html += (
            f'<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; opacity: {opacity};">'
            f'<span style="font-family: inherit; font-size: 12px; color: {color}; font-weight: {weight};">{lbl_display}</span>'
            f'<div style="display: flex; align-items: center; width: 60%; gap: 8px;">'
            f'<div style="background: rgba(128, 128, 128, 0.1); border-radius: 4px; height: 6px; flex-grow: 1; overflow: hidden; border: 1px solid rgba(128, 128, 128, 0.1);">'
            f'<div style="background: {bar_color}; height: 100%; width: {bar_width}; border-radius: 4px;"></div>'
            f'</div>'
            f'<span style="min-width: 45px; text-align: right; font-family: monospace; font-size: 11px; color: {color}; font-weight: {weight};">{prob:.1%}</span>'
            f'</div>'
            f'</div>'
        )
        
    if source == "Local Classifier":
        source_badge = (
            f'<span style="font-size: 11px; padding: 4px 10px; border-radius: 20px; '
            f'background: rgba(0, 229, 255, 0.12); border: 1px solid rgba(0, 229, 255, 0.3); '
            f'color: #00e5ff; font-weight: 600; letter-spacing: 0.5px;">⚡ {source}</span>'
        )
        confidence_val = f"{local_confidence:.1%}"
        progress_width = f"{local_confidence * 100:.1f}%"
        progress_bar_color = "linear-gradient(90deg, #00e5ff, #0077ff)"
    else:
        # LLM Fallback
        source_badge = (
            f'<span style="font-size: 11px; padding: 4px 10px; border-radius: 20px; '
            f'background: rgba(255, 0, 127, 0.12); border: 1px solid rgba(255, 0, 127, 0.3); '
            f'color: #ff007f; font-weight: 600; letter-spacing: 0.5px;">🤖 {source}</span>'
        )
        confidence_val = "LLM Overrode"
        progress_width = "100%"
        progress_bar_color = "linear-gradient(90deg, #ff007f, #7f00ff)"
        
    fallback_note = ""
    if source != "Local Classifier":
        local_intent_display = local_intent.replace("_", " ").title()
        fallback_note = (
            f'<div style="font-size: 12px; color: #ff55a3; margin-bottom: 10px; padding: 6px 10px; '
            f'background: rgba(255, 0, 127, 0.05); border-left: 3px solid #ff007f; border-radius: 0 6px 6px 0;">'
            f'⚠️ Local Classifier confidence ({local_confidence:.1%}) for <b>{local_intent_display}</b> was '
            f'below threshold (75.0%). Re-routing request to Gemini LLM.</div>'
        )
        
    html_content = f"""
<div style="background: rgba(128, 128, 128, 0.08); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 14px; margin-top: 12px; margin-bottom: 8px; max-width: 550px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
<span style="font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85;">🔮 Intent Routing Engine</span>
{source_badge}
</div>
{fallback_note}
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 13px; opacity: 0.75;">Routed Intent:</span>
<span style="font-family: monospace; font-size: 13px; font-weight: bold; background: rgba(128, 128, 128, 0.15); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(128, 128, 128, 0.2);">{intent_display}</span>
</div>
<span style="font-weight: 700; font-size: 13px; color: #00e5ff;">{confidence_val}</span>
</div>
<div style="background: rgba(128, 128, 128, 0.1); border-radius: 10px; height: 5px; width: 100%; overflow: hidden; margin-bottom: 14px; border: 1px solid rgba(128, 128, 128, 0.05);">
<div style="background: {progress_bar_color}; height: 100%; width: {progress_width};"></div>
</div>
<details style="font-size: 12px; cursor: pointer; border-top: 1px solid rgba(128, 128, 128, 0.15); padding-top: 8px;">
<summary style="outline: none; margin-bottom: 6px; font-weight: 500; font-size: 12px; opacity: 0.85;">📈 View Intent Confidence Scores</summary>
<div style="margin-top: 6px; display: grid; gap: 4px; background: rgba(128, 128, 128, 0.05); padding: 10px; border-radius: 8px;">
{breakdown_html}
</div>
</details>
</div>
"""
    # Uncomment the line below to show the Intent Routing Engine box during your demo!
    # st.markdown(html_content, unsafe_allow_html=True)

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
                    
                    if "intent_details" in content:
                        render_intent_details(content["intent_details"])
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
                    
                    if "intent_details" in response:
                        render_intent_details(response["intent_details"])
            except Exception as e:
                st.error("Error communicating with the backend API. Is FastAPI running?")

if __name__ == "__main__":
    main()
