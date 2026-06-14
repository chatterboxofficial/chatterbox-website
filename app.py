from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_name = data.get('name', 'User')
    message = data.get('message')
    
    # Yahan API call aayegi, abhi ke liye simple response
    reply = f"Hello {user_name}, I am your AI assistant. You said: {message}"
    
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run()
