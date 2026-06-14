from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

# This pulls the key you saved in Render Environment Variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": user_message}]
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response_data = response.json()
        
        # Check if the API returned an error
        if "choices" in response_data:
            reply = response_data["choices"][0]["message"]["content"]
        else:
            reply = "AI API Error: " + str(response_data)
            
    except Exception as e:
        reply = "System Error: Unable to connect to AI."
        
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
