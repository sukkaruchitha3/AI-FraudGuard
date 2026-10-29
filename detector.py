from email import message
import os
import string
import re

import pandas as pd
import joblib
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from train import build_detector_model

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "scam_detector.joblib")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "scam_vectorizer.joblib")

os.makedirs(MODELS_DIR, exist_ok=True)

nltk.download("stopwords", quiet=True)
try:
    stop_words = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords", quiet=True)
    stop_words = set(stopwords.words("english"))


def preprocess(text):
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = [word for word in text.split() if word not in stop_words]
    return " ".join(words)


def ensure_detector_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        print("[detector.py] Training detector model because saved model is missing...")
        build_detector_model()

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return model, vectorizer


model, vectorizer = ensure_detector_model()

persuasion_keywords = {
    "urgency": ["urgent", "immediately", "act now", "limited time", "hurry"],
    "guaranteed_return": ["guaranteed", "double money", "risk free", "sure profit"],
    "fomo": ["limited offer", "only today", "don\'t miss", "last chance"],
    "authority": ["bank", "rbi", "official", "we are from"],
    "payment_request": ["send money", "transfer now", "pay fee", "account details"],
    "crypto": ["bitcoin", "crypto", "trading group"],
    "otp": ["otp", "verification code"],
    "loan_app": ["instant loan", "quick loan"],
    "upi_request": ["upi collect", "payment request"]
}

category_keywords = {
    "Lottery Scam": ["won", "prize", "congratulations", "winner"],
    "Loan Scam": ["loan approval", "easy loan", "instant loan", "pre approved"],
    "Investment Scam": ["profit", "returns", "investment offer", "high yield"],
    "Phishing": ["verify account", "click link", "password", "login details"],
    "UPI Fraud": ["upi collect", "send money", "payment request", "transaction request"],
    "Account Takeover": ["suspend account", "verify identity", "reconfirm", "security alert"],
    "Crypto Scam": ["crypto", "bitcoin", "trading profit"],
    "OTP Fraud": ["otp", "verification code"],
    "Loan Scam": ["loan approval", "instant loan"],
    "Investment Scam": ["profit", "returns", "double money"],
    "Phishing": ["verify account", "click link"],
    "UPI Fraud": ["upi collect", "payment request"],
    "Lottery Scam": ["won", "prize", "winner"],
    "Delivery Scam": [
    "delivery fee",
    "tracking number",
    "reschedule delivery",
    "parcel held",
    "shipment update"]

}



def detect_category(text):
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text.lower():
                return category
    return "General Fraud Alert"


def detect_persuasion(text):
    detected = []
    for technique, keywords in persuasion_keywords.items():
        for word in keywords:
            if word in text.lower() and technique not in detected:
                detected.append(technique)
    return detected

import re

def contains_suspicious_link(text):

    url_pattern = r"(https?://\S+|www\.\S+)"

    suspicious_domains = [
        "bit.ly",
        "tinyurl",
        "update",
        "verify",
        "secure",
        "account",
        "delivery",
        "shipment"
    ]

    urls = re.findall(url_pattern, text.lower())

    for url in urls:

        for keyword in suspicious_domains:

            if keyword in url:
                return True

    return False


def analyze_message(message):

    cleaned = preprocess(message)

    vector = vectorizer.transform([cleaned])

    prediction = model.predict(vector)[0]

    probability = model.predict_proba(vector).max()

    score = int(probability * 100)


    financial_scam_keywords = [

    "otp",
    "crypto",
    "investment",
    "loan approval",
    "guaranteed return",
    "double money",
    "upi collect",
    "click link",
    "verify account",
    "limited offer",

    "delivery fee",
    "reschedule delivery",
    "tracking number",
    "payment request",
    "confirm shipment",
    "parcel held",
    "customs charge"
]


    persuasion_patterns = detect_persuasion(message)

    category = detect_category(message)


    keyword_flag = any(word in message.lower() for word in financial_scam_keywords)
    link_flag = contains_suspicious_link(message)


    if prediction.lower() == "spam" or keyword_flag or link_flag:

        status = "HIGH RISK"

        explanation = "This message contains financial scam indicators."

    else:

        status = "SAFE"

        explanation = "No strong scam indicators detected."


    return {

        "score": score,
        "status": status,
        "category": category,
        "persuasion": persuasion_patterns,
        "explanation": explanation

    }
