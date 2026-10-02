import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

def embed_model():
    return settings.GEMINI_EMBED_MODEL

def chat_model():
    return genai.GenerativeModel(settings.GEMINI_CHAT_MODEL)