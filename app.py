from flask import Flask, render_template, request, jsonify
import requests
import google.generativeai as genai
import os
import json

app = Flask(__name__)

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyAiUgrfo1SwtreEoFodufI-SZnB2v1eiCo"
genai.configure(api_key=GEMINI_API_KEY)

# Robust Model Selection
def get_model():
    # Try multiple common name patterns for compatibility
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro', 'models/gemini-pro']
    for m in models_to_try:
        try:
            model = genai.GenerativeModel(m)
            # Basic test call
            model.generate_content("test") 
            print(f"  Gemini successfully bound to model: {m}")
            return model
        except Exception as e:
            print(f"  Warning: Failed to bind to model {m}: {e}")
            continue
    
    # Final fallback if all else fails
    print("  CRITICAL: No accessible models found! Voice bot will be offline.")
    return None

model = get_model()

# ESP32 Configuration - Update this IP to your ESP32's IP address
ESP32_IP = os.environ.get("ESP32_IP", "192.168.1.100")
ESP32_PORT = os.environ.get("ESP32_PORT", "80")
ESP32_URL = f"http://{ESP32_IP}:{ESP32_PORT}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/temperature', methods=['GET'])
def get_temperature():
    """Proxy endpoint to fetch temperature from ESP32"""
    try:
        response = requests.get(f"{ESP32_URL}/temperature", timeout=3)
        data = response.json()
        return jsonify({
            "success": True,
            "temperature": data.get("temperature", data.get("temp", 0)),
            "humidity": data.get("humidity", data.get("hum", 0)),
            "unit": "C",
            "source": "ESP32"
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "temperature": None,
            "error": "ESP32 not connected",
            "demo": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "temperature": None,
            "error": str(e),
            "demo": True
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Gemini AI chat endpoint with object detection context"""
    try:
        body = request.get_json()
        user_message = body.get('message', '')
        detected_objects = body.get('detectedObjects', [])
        temperature = body.get('temperature', None)
        location = body.get('location', None)
        
        # Build rich context from detection data
        context_parts = []
        
        if detected_objects:
            obj_summary = []
            for obj in detected_objects:
                obj_summary.append(f"{obj.get('class', 'unknown')} (confidence: {obj.get('score', 0)*100:.1f}%)")
            context_parts.append(f"Currently detected objects in the camera: {', '.join(obj_summary)}.")
        else:
            context_parts.append("No objects are currently detected in the camera frame.")
        
        if temperature:
            context_parts.append(f"Room temperature from ESP32 sensor: {temperature}°C.")
        
        if location:
            context_parts.append(f"Device location: Latitude {location.get('lat', 'unknown')}, Longitude {location.get('lon', 'unknown')}.")
        
        context = " ".join(context_parts)
        
        system_prompt = f"""You are ARIA (Adaptive Real-time Intelligence Assistant), an AI assistant integrated into a smart surveillance and monitoring system. 

CURRENT ENVIRONMENT DATA:
{context}

Your role:
- Answer questions about the detected objects in the camera
- Provide insights about the room environment and temperature
- Help identify people, objects, and analyze the scene
- Give security alerts if suspicious activity is detected
- Be concise, clear and helpful
- If asked about the temperature, humidity, or location, reference the sensor data above
- Keep responses under 3 sentences for voice output clarity"""

        full_prompt = f"{system_prompt}\n\nUser question: {user_message}"
        
        response = model.generate_content(full_prompt)
        reply = response.text.strip()
        
        return jsonify({
            "success": True,
            "reply": reply
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Chat Error: {error_msg}")
        return jsonify({
            "success": False,
            "reply": f"Neural Link Error: {error_msg}. Please ensure your Gemini API key is valid and the Generative Language API is enabled.",
            "error": error_msg
        })

@app.route('/api/analyze', methods=['POST'])
def analyze_scene():
    """Analyze the complete scene and provide a summary"""
    try:
        body = request.get_json()
        detected_objects = body.get('detectedObjects', [])
        temperature = body.get('temperature', None)
        location = body.get('location', None)
        
        if not detected_objects:
            return jsonify({
                "success": True,
                "analysis": "The camera feed appears to be empty. No objects or people are currently detected in view."
            })
        
        obj_list = []
        person_count = 0
        for obj in detected_objects:
            cls = obj.get('class', 'unknown')
            score = obj.get('score', 0) * 100
            obj_list.append(f"{cls} ({score:.0f}% confidence)")
            if cls.lower() == 'person':
                person_count += 1
        
        prompt = f"""Analyze this surveillance scene and provide a brief security/monitoring summary:
        
Detected objects: {', '.join(obj_list)}
Number of people detected: {person_count}
Room temperature: {temperature}°C if available
Location: {location}

Provide a 2-3 sentence professional scene analysis covering what's happening, any notable observations, and the environment status. Be concise for text-to-speech."""
        
        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "analysis": response.text.strip()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "analysis": f"Analysis unavailable: {str(e)}"
        })

if __name__ == '__main__':
    print("=" * 60)
    print("  ARIA - Smart Surveillance System")
    print("=" * 60)
    print(f"  ESP32 Target: {ESP32_URL}")
    print(f"  Gemini AI: {'Configured' if GEMINI_API_KEY != 'YOUR_GEMINI_API_KEY_HERE' else 'NOT CONFIGURED'}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
