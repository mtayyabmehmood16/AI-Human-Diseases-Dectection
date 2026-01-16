from src.ai_client import AIClient
import os

# Use the key from main.py for testing
API_KEY = "AIzaSyBb56ch7_fbimK5712ZjyV6zy_deqzwt7o"

print("Initializing AI Client...")
client = AIClient(api_key=API_KEY)
print(f"Model: {client.model_name}")

try:
    print("Sending test request...")
    response = client.generate_content("Explain the medical term 'tachycardia' in one sentence.")
    print(f"SUCCESS: AI Response: {response}")
except Exception as e:
    print(f"FAILURE: AI Error: {e}")
