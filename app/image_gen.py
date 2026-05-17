import urllib.parse
import uuid
import os
import requests

def generate_image_url(prompt: str) -> str:
    """
    Generates an image using Pollinations.ai by downloading it backend-side with a real User-Agent.
    Returns the local filepath to the image so Streamlit can render it safely.
    """
    encoded_prompt = urllib.parse.quote(prompt)
    seed = uuid.uuid4().hex[:8]
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024"
    
    # Download the image using a browser user-agent to bypass 403 Forbidden blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    filename = f"generated_img_{seed}.jpg"
    filepath = os.path.join(os.getcwd(), filename)
    
    with open(filepath, "wb") as f:
        f.write(response.content)
        
    return filepath
