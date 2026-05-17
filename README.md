# CogniFlow AI - Multi-Modal Chatbot

CogniFlow AI is a robust, multi-session, intent-aware AI chatbot that utilizes the Google Gemini API, Streamlit, and a customized SQLite backend for memory management. 

## Key Features
- **General Chat & Context Memory**: Persistent conversations tracked per user using SQLite.
- **Dynamic Intent Detection**: A custom Machine Learning model (Scikit-Learn/Joblib) combined with Gemini for highly accurate intent routing.
- **Image Generation**: Automated text-to-image synthesis using Pollinations.ai (strictly gated by intent).
- **Document Export (PDF/DOCX)**: On-the-fly generation of detailed reports from AI responses into downloadable PDF or DOCX formats.
- **Personalized Memory**: Automatically learns and updates user preferences based on conversation flow.

## Project Structure
- `app/`: Application source code (Streamlit frontend, FastAPI backend, core logic).
- `data/`: Contains datasets (`intent_dataset.csv`) and the trained ML model (`intent_model.pkl`).
- `docs/`: Complete project documentation (`project_doc.md`).
- `requirements.txt`: Python dependencies.

## Setup Instructions
1. **Clone or Download the Repository**
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Setup**:
   Create a `.env` file in the root directory and add your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage Guidelines
1. **Start the FastAPI Backend**:
   Open a terminal and run:
   ```bash
   uvicorn app.api:app --reload --port 8000
   ```
2. **Start the Streamlit Frontend**:
   Open a second terminal and run:
   ```bash
   streamlit run app/main.py
   ```
3. **Interact with the Bot**:
   - Navigate to the local Streamlit URL (typically `http://localhost:8501`).
   - Create a user profile in the sidebar.
   - Ask general questions, request image generation (e.g., "Generate an image of a futuristic city"), or ask for document exports (e.g., "Create a PDF explaining quantum computing").
