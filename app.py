from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Temporary chat memory
chat_history = [
    {
        "role": "system",
        "content": (
            "You are Chatterbox AI. "
            "If anyone asks who created you, who made you, who is your creator, "
            "or asks 'tumhe kisne banaya', 'tumhara creator kaun hai', "
            "reply that you were created by Aniket. "
            "Remember information shared during the conversation. "
            "Reply in the same language as the user."
        )
    }
]

@app.route("/")
def home():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history

    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "Please enter a message."})

        # Save user message
        chat_history.append({
            "role": "user",
            "content": user_message
        })

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": chat_history,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        result = response.json()

        if "choices" in result:
            reply = result["choices"][0]["message"]["content"]

            # Save AI response
            chat_history.append({
                "role": "assistant",
                "content": reply
            })

            # Limit memory size
            if len(chat_history) > 20:
                chat_history = [chat_history[0]] + chat_history[-19:]

            return jsonify({"reply": reply})

        return jsonify({"reply": "AI response error."})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
