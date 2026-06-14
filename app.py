import os, requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def home(): return send_from_directory(".", "index.html")

@app.route("/chat.html")
def chat_page(): return send_from_directory(".", "chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", 
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": f"You are Chatterbox AI, assistant to {data.get('name', 'User')}. Be professional and concise."},
                             {"role": "user", "content": data.get("message", "")}]
            })
        return jsonify({"reply": res.json()["choices"][0]["message"]["content"]})
    except: return jsonify({"reply": "System Error: Please try again."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

