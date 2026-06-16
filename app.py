from flask import Flask, render_template, request, jsonify
import os
import requests
import base64
import PyPDF2
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'png', 'jpg', 'jpeg', 'webp'}

# ─────────────────────────────────────────────
# SYSTEM PROMPTS FOR EACH MODE
# ─────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "general": (
        "You are Chatterbox AI, a powerful and friendly AI assistant created by Aniket. "
        "If anyone asks who created you or who made you, always say 'I was created by Aniket.' "
        "You can help with anything — studies, research, coding, content creation, personal life, and more. "
        "Reply in the same language the user uses (Hindi or English). "
        "Remember information shared during the conversation. "
        "Be helpful, friendly, and give detailed answers."
    ),
    "student": (
        "You are Chatterbox AI in Student Mode, created by Aniket. "
        "You are an expert tutor who helps students with all subjects. "
        "Explain concepts clearly with examples, step-by-step solutions, and simple language. "
        "Help with homework, assignments, quizzes, notes, and exam preparation. "
        "If an image is provided, analyze it carefully and solve the question shown. "
        "Reply in the same language the user uses (Hindi or English). "
        "Be encouraging and patient with students."
    ),
    "research": (
        "You are Chatterbox AI in Deep Research Mode, created by Aniket. "
        "You are an expert researcher and analyst. "
        "Provide deep, detailed, well-structured research on any topic. "
        "Break down complex topics, provide multiple perspectives, cite key facts, and give thorough analysis. "
        "Use headings, subheadings, bullet points, and structured format in your responses. "
        "Think step by step and explain your reasoning. "
        "Reply in the same language the user uses (Hindi or English)."
    ),
    "thinking": (
        "You are Chatterbox AI in Thinking Mode, created by Aniket. "
        "For every question, think deeply and show your step-by-step reasoning process. "
        "Format your response as: "
        "🧠 THINKING PROCESS: (show your step by step analysis) "
        "💡 CONCLUSION: (give the final answer) "
        "📊 CONFIDENCE: (how confident you are and why) "
        "Be thorough, logical, and analytical. "
        "Reply in the same language the user uses (Hindi or English)."
    ),
    "creator": (
        "You are Chatterbox AI in Creator Mode, created by Aniket. "
        "You are an expert social media strategist and content creator. "
        "Help with: YouTube scripts, video ideas, titles, descriptions, tags, thumbnails concepts. "
        "Instagram captions, reels ideas, hashtags, bio writing. "
        "Blog posts, articles, newsletters. "
        "Content calendars, posting schedules, growth strategies. "
        "Data analysis for creator metrics (views, engagement, growth). "
        "Work and task tracking for content creators. "
        "Reply in the same language the user uses (Hindi or English). "
        "Be creative, trendy, and practical."
    ),
    "coding": (
        "You are Chatterbox AI in Coding Mode, created by Aniket. "
        "You are an expert software developer and coding assistant. "
        "Help with: writing code in any language, debugging errors, code review, "
        "explaining code, suggesting best practices, architecture design, "
        "Git/GitHub help, deployment issues, API integration, database design. "
        "Always provide clean, well-commented code with explanations. "
        "When fixing bugs, explain what was wrong and why your fix works. "
        "Reply in the same language the user uses (Hindi or English)."
    ),
    "personal": (
        "You are Chatterbox AI in Personal Assistant Mode, created by Aniket. "
        "You are a caring, supportive personal life assistant. "
        "Help with: daily planning, goal setting, habit tracking, motivation, "
        "life advice, decision making, stress management, productivity tips, "
        "relationship advice, health and wellness guidance, journaling prompts. "
        "Be empathetic, supportive, and non-judgmental. "
        "Remember personal details shared during the conversation. "
        "Reply in the same language the user uses (Hindi or English). "
        "Be warm, friendly, and encouraging."
    ),
}

# Store chat histories per mode (in production, use a database)
chat_histories = {mode: [{"role": "system", "content": prompt}]
                  for mode, prompt in SYSTEM_PROMPTS.items()}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_bytes):
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text[:8000]  # Limit to avoid token overflow
    except Exception as e:
        return f"Could not read PDF: {str(e)}"


def call_groq_text(messages, model="llama-3.3-70b-versatile", max_tokens=2048):
    """Call Groq API for text responses."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    result = response.json()
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    return None


def call_groq_vision(messages, max_tokens=2048):
    """Call Groq Vision API for image analysis."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    result = response.json()
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    return None


def trim_history(history, max_size=20):
    """Keep system prompt + last N messages to avoid token overflow."""
    if len(history) > max_size:
        return [history[0]] + history[-(max_size - 1):]
    return history


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint — handles text messages for all modes."""
    global chat_histories
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        mode = data.get("mode", "general")

        if not user_message:
            return jsonify({"reply": "Please enter a message."})

        if mode not in chat_histories:
            mode = "general"

        # Add user message to history
        chat_histories[mode].append({"role": "user", "content": user_message})

        # Choose model based on mode
        model = "llama-3.3-70b-versatile"
        if mode == "thinking":
            model = "llama-3.3-70b-versatile"
        elif mode == "coding":
            model = "llama-3.3-70b-versatile"
        else:
            model = "llama-3.1-8b-instant" if mode == "personal" else "llama-3.3-70b-versatile"

        reply = call_groq_text(chat_histories[mode], model=model)

        if reply:
            chat_histories[mode].append({"role": "assistant", "content": reply})
            chat_histories[mode] = trim_history(chat_histories[mode])
            return jsonify({"reply": reply})

        return jsonify({"reply": "AI response error. Please try again."})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})


@app.route("/chat/image", methods=["POST"])
def chat_image():
    """Handle image upload for vision analysis (Snap & Solve)."""
    global chat_histories
    try:
        mode = request.form.get("mode", "student")
        user_message = request.form.get("message", "Solve this question or describe what you see in this image.").strip()

        if 'image' not in request.files:
            return jsonify({"reply": "No image provided."})

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"reply": "No image selected."})

        # Read and encode image to base64
        image_bytes = image_file.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        ext = image_file.filename.rsplit('.', 1)[-1].lower()
        media_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

        # Build vision message
        vision_messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["student"])
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ]

        reply = call_groq_vision(vision_messages)

        if reply:
            # Also save to mode history as text
            chat_histories[mode].append({"role": "user", "content": f"[Image uploaded] {user_message}"})
            chat_histories[mode].append({"role": "assistant", "content": reply})
            chat_histories[mode] = trim_history(chat_histories[mode])
            return jsonify({"reply": reply})

        return jsonify({"reply": "Could not analyze image. Please try again."})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})


@app.route("/chat/file", methods=["POST"])
def chat_file():
    """Handle file upload (PDF/TXT) and answer questions about it."""
    global chat_histories
    try:
        mode = request.form.get("mode", "student")
        user_message = request.form.get("message", "Summarize this file and give key points.").strip()

        if 'file' not in request.files:
            return jsonify({"reply": "No file provided."})

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({"reply": "No file selected."})

        if not allowed_file(uploaded_file.filename):
            return jsonify({"reply": "Only PDF, TXT, and image files are supported."})

        file_bytes = uploaded_file.read()
        ext = uploaded_file.filename.rsplit('.', 1)[-1].lower()

        if ext == 'pdf':
            file_text = extract_text_from_pdf(file_bytes)
            file_context = f"The user has uploaded a PDF file. Here is its content:\n\n{file_text}\n\nUser's question: {user_message}"
        elif ext == 'txt':
            file_text = file_bytes.decode('utf-8', errors='ignore')[:8000]
            file_context = f"The user has uploaded a text file. Here is its content:\n\n{file_text}\n\nUser's question: {user_message}"
        elif ext in ['png', 'jpg', 'jpeg', 'webp']:
            # Redirect to vision
            image_b64 = base64.b64encode(file_bytes).decode('utf-8')
            media_type = f"image/{'jpeg' if ext == 'jpg' else ext}"
            vision_messages = [
                {"role": "system", "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["student"])},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}},
                        {"type": "text", "text": user_message}
                    ]
                }
            ]
            reply = call_groq_vision(vision_messages)
            if reply:
                return jsonify({"reply": reply})
            return jsonify({"reply": "Could not analyze image file."})
        else:
            return jsonify({"reply": "Unsupported file type."})

        # Add file context to chat
        messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["general"])}]
        messages.append({"role": "user", "content": file_context})

        reply = call_groq_text(messages, model="llama-3.3-70b-versatile", max_tokens=2048)

        if reply:
            chat_histories[mode].append({"role": "user", "content": f"[File uploaded: {uploaded_file.filename}] {user_message}"})
            chat_histories[mode].append({"role": "assistant", "content": reply})
            chat_histories[mode] = trim_history(chat_histories[mode])
            return jsonify({"reply": reply})

        return jsonify({"reply": "Could not process file. Please try again."})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})


@app.route("/image/generate", methods=["POST"])
def generate_image():
    """Generate image using Pollinations AI (completely free, no API key needed)."""
    try:
        data = request.get_json()
        prompt = data.get("prompt", "").strip()

        if not prompt:
            return jsonify({"error": "Please provide an image prompt."})

        # Pollinations AI — free, no API key needed
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"

        return jsonify({"image_url": image_url, "prompt": prompt})

    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})


@app.route("/clear", methods=["POST"])
def clear_history():
    """Clear chat history for a specific mode."""
    global chat_histories
    try:
        data = request.get_json()
        mode = data.get("mode", "general")

        if mode in SYSTEM_PROMPTS:
            chat_histories[mode] = [{"role": "system", "content": SYSTEM_PROMPTS[mode]}]
            return jsonify({"status": "cleared", "mode": mode})

        return jsonify({"status": "error", "message": "Invalid mode"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/modes", methods=["GET"])
def get_modes():
    """Return available modes."""
    modes = [
        {"id": "general", "name": "💬 General Chat", "description": "General AI assistant"},
        {"id": "student", "name": "🎓 Student Mode", "description": "Homework, quizzes, notes"},
        {"id": "research", "name": "🔍 Deep Research", "description": "In-depth research & analysis"},
        {"id": "thinking", "name": "🧠 Thinking Mode", "description": "Step-by-step reasoning"},
        {"id": "creator", "name": "🎨 Creator Mode", "description": "YouTube, Instagram, content"},
        {"id": "coding", "name": "💻 Coding Mode", "description": "Code help & debugging"},
        {"id": "personal", "name": "🌟 Personal Assistant", "description": "Life planning & advice"},
    ]
    return jsonify({"modes": modes})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
