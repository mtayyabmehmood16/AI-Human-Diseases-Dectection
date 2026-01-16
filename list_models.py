import google.generativeai as genai
import os

API_KEY = "AIzaSyD5Aw1i8VRyij0sw64INFoUc7FAgfnT2m0"
genai.configure(api_key=API_KEY)

try:
    print("Listing models...")
    for m in genai.list_models():
        print(f"Name: {m.name}, Supported: {m.supported_generation_methods}")
except Exception as e:
    print("Error listing models:", e)
