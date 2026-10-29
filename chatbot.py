from transformers import pipeline

chatbot_model = None


def load_model():
    global chatbot_model

    if chatbot_model is None:
        print("Loading chatbot model...")
        chatbot_model = pipeline(
            "text-generation",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            device_map="auto"
        )
        print("Chatbot ready.")


SYSTEM_PROMPT = """
You are a helpful financial safety advisor.

Explain scams clearly.
Warn users about phishing, crypto scams, OTP fraud, fake loan apps.
Give safe financial guidance.
Answer in 4–6 simple sentences.
"""


def chatbot_response(user_msg):

    if not user_msg:
        return "Please type a question."

    load_model()

    prompt = f"<|system|>\n{SYSTEM_PROMPT}\n<|user|>\n{user_msg}\n<|assistant|>"

    response = chatbot_model(
        prompt,
        max_new_tokens=150,
        temperature=0.7
    )

    output = response[0]["generated_text"]

    return output.split("<|assistant|>")[-1].strip()


def build_chatbot_knowledge_base():
    print("Chatbot initialized successfully.")