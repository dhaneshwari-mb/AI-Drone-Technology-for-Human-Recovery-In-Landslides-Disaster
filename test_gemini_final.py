import google.generativeai as genai
import os

API_KEY = "AIzaSyAiUgrfo1SwtreEoFodufI-SZnB2v1eiCo"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

try:
    response = model.generate_content("hello")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILED with error: {e}")
