import os
import io
import tempfile
import hashlib
from openai import OpenAI
from pathlib import Path
import base64

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cache directory
CACHE_DIR = os.path.join(tempfile.gettempdir(), "insight_tts_cache")

def get_cache_path(text_content):
    """Generate a cache file path based on content hash"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    # Create hash from text content
    content_hash = hashlib.md5(text_content.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"{content_hash}.mp3")

def text_to_speech(text, voice="echo", model="tts-1"):
    """
    Convert text to speech using OpenAI's TTS API
    
    Args:
        text (str): The text to convert to speech
        voice (str): The voice to use (default: "echo")
        model (str): The model to use (default: "tts-1")
        
    Returns:
        str: Path to the audio file that can be used by Gradio
    """
    try:
        # Check if we have a cached version
        cache_path = get_cache_path(text)
        if os.path.exists(cache_path):
            # Return cached audio file path
            return cache_path

        # If not cached, call OpenAI API
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # Save to cache file
        response.stream_to_file(cache_path)
        
        # Return the file path for Gradio
        return cache_path
            
    except Exception as e:
        print(f"Error in text_to_speech: {str(e)}")
        return None
