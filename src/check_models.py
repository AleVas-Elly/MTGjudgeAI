from google import genai
import keyring
import os
from dotenv import load_dotenv

SERVICE_NAME = "mtg_rulebook_ai"
USERNAME = "gemini_api_key"

def get_api_key():
    api_key = keyring.get_password(SERVICE_NAME, USERNAME)
    if not api_key:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
    return api_key

def list_models():
    api_key = get_api_key()
    if not api_key:
        print("❌ No API key found.")
        return
    
    client = genai.Client(api_key=api_key)
    print("Listing available models...")
    try:
        # Note: listing models might not be directly available in the same way in all SDK versions
        # but we can try to see what's allowed.
        # For now, let's just try to call a standard model.
        models = client.models.list()
        for m in models:
            print(f"- {m.name} ({m.display_name})")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_models()
