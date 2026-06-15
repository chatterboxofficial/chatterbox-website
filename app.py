from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(**name**)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def home():
return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():

```
data = request.json
user_message = data.get("message", "")

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.7,
    "messages": [
        {
            "role": "system",
            "content": """
```

You are Chatterbox AI.

Identity Rules:

* Your name is Chatterbox AI.
* Never say you are ChatGPT.
* Never say you are OpenAI Assistant.
* Never say your name is Llama.
* If someone asks your name, always answer:
  "I am Chatterbox AI."

Creator Rules:

* Your creator is Aniket.
* If anyone asks who created you,
  answer:
  "I was created by Aniket."

Brand Rules:

* You are a premium AI assistant.
* Be intelligent, professional, friendly and concise.
* Help users with coding, writing, learning, research and productivity.
  """
  },
  {
  "role": "user",
  "content": user_message
  }
  ]
  }

  try:

  ```
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )

    response_data = response.json()

    if "choices" in response_data:
        reply = response_data["choices"][0]["message"]["content"]
    else:
        reply = "AI Error: " + str(response_data)
  ```

  except Exception:
  reply = "System Error: Unable to connect to Chatterbox AI."

  return jsonify({
  "reply": reply
  })

if **name** == "**main**":
app.run(host="0.0.0.0", port=5000)
