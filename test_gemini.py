import google.generativeai as genai
import sys
import traceback

API_KEY = "AIzaSyAiUgrfo1SwtreEoFodufI-SZnB2v1eiCo"

def diagnose():
    print(f"Python: {sys.version}")
    try:
        import google.generativeai as genai
        print(f"google-generativeai version: {genai.__version__}")
    except ImportError:
        print("google-generativeai NOT INSTALLED")
        return

    try:
        genai.configure(api_key=API_KEY)
        print("Models available for generateContent:")
        models = genai.list_models()
        count = 0
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
                count += 1
        if count == 0:
            print("No suitable models found. Check API key permissions.")
    except Exception as e:
        print(f"Error during model listing: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
