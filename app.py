from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    # Flask automatically looks inside the 'templates' folder
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_name = data.get('name', 'User')
    message = data.get('message')
    
    # AI logic yahan aayegi
    reply = f"Hello {user_name}, I am your AI assistant. You said: {message}"
    
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
