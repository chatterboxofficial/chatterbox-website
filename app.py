
import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Groq API Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/chat.html")
def chat_page():
    return send_from_directory(".", "chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    # Groq API call
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are Chatterbox AI, a helpful personal assistant. If asked your name, you are Chatterbox AI."},
            {"role": "user", "content": user_message}
        ]
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        res_data = response.json()
        ai_reply = res_data["choices"][0]["message"]["content"]
        return jsonify({"reply": ai_reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
