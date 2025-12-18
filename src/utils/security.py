import os
import sys
import keyring
from src.config import SERVICE_NAME, USERNAME

def get_api_key():
    """Retrieves the API key from keychain or environment."""
    api_key = keyring.get_password(SERVICE_NAME, USERNAME)
    
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("\nAPI Key not found in Keychain or environment.")
        api_key = input("Enter Groq API Key: ").strip()
        if not api_key:
            print("Error: API Key is required.")
            sys.exit(1)
        
        try:
            keyring.set_password(SERVICE_NAME, USERNAME, api_key)
            print("Key saved to System Keychain.")
        except Exception as e:
            print(f"Warning: Could not save to keychain: {e}")

    return api_key
