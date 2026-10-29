from chatbot import chatbot_response
from flask import Flask, render_template, request
from detector import analyze_message

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        message = request.form["message"]
        result = analyze_message(message)
        return render_template("result.html", result=result, message=message)

    return render_template("index.html")

@app.route("/chatbot", methods=["POST"])
def chatbot():

    user_msg = request.form.get("message")

    print("User message received:", user_msg)   # DEBUG LINE

    if not user_msg:
        return {"response": "Please type something."}

    reply = chatbot_response(user_msg)

    return {"response": reply}

if __name__ == "__main__":
    app.run(debug=True)