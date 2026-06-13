from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data["message"]

    response = model.generate_content(
        f"You are ChatterBox AI. Reply helpfully.\nUser: {msg}"
    )

    return jsonify({"reply": response.text})

@app.route("/")
def home():
    return "ChatterBox AI Running"

if __name__ == "__main__":
    app.run()
