import os
import re
import string
import pandas as pd
import joblib
import nltk

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from chatbot import build_chatbot_knowledge_base

DATA_DIR = os.path.join(os.path.dirname(__file__), "dataset")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

MODEL_PATH = os.path.join(MODELS_DIR, "scam_detector.joblib")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "scam_vectorizer.joblib")

os.makedirs(MODELS_DIR, exist_ok=True)


def get_stopwords():
    try:
        return set(nltk.corpus.stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        return set(nltk.corpus.stopwords.words("english"))


def preprocess(text):
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = [word for word in text.split() if word not in get_stopwords()]
    return " ".join(words)


def load_scam_file(path):
    labels = {"spam", "ham", "scam", "safe"}
    rows = []

    with open(path, encoding="latin-1", errors="replace") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        return pd.DataFrame(columns=["label", "message"])

    header = lines[0].lower()
    if any(name in header for name in ["text,label", "message,label", "label,text", "label,message", "v1,v2"]):
        lines = lines[1:]

    for line in lines:
        if "\t" in line:
            parts = line.split("\t")
        else:
            parts = line.rsplit(",", 1)

        if len(parts) != 2:
            continue

        left = parts[0].strip()
        right = parts[1].strip()

        if right.lower() in labels:
            label = right.lower()
            message = left
        elif left.lower() in labels:
            label = left.lower()
            message = right
        else:
            continue

        rows.append((label, message))

    data = pd.DataFrame(rows, columns=["label", "message"])
    data = data[data["message"].notna()]
    data["label"] = data["label"].astype(str).str.strip().str.lower()
    data = data[data["label"].isin(labels)]
    data["label"] = data["label"].replace({"ham": "safe", "scam": "spam"})
    return data


def collect_scam_datasets():
    all_data = []
    for name in os.listdir(DATA_DIR):
        lower = name.lower()
        path = os.path.join(DATA_DIR, name)
        if not os.path.isfile(path):
            continue
        if lower.endswith(".csv") and ("spam" in lower or "scam" in lower or name == "spam.csv"):
            try:
                all_data.append(load_scam_file(path))
            except Exception:
                continue
        if lower == "smsspamcollection" or lower.endswith(".txt") and "spam" in lower:
            try:
                all_data.append(load_scam_file(path))
            except Exception:
                continue

    if not all_data:
        raise FileNotFoundError("No scam dataset file could be loaded from the dataset folder.")

    return pd.concat(all_data, ignore_index=True)


def build_detector_model():
    print("[train.py] Preparing scam detector training data...")
    data = collect_scam_datasets()

    extra_data_path = os.path.join(DATA_DIR, "financial_traps.csv")

    if os.path.exists(extra_data_path):
        extra_df = pd.read_csv(extra_data_path)
        data = pd.concat([data, extra_df], ignore_index=True)

    safe_examples = [
        "Happy birthday! Hope your day is wonderful and safe.",
        "See you at the meeting tomorrow morning.",
        "Your appointment is confirmed for Friday.",
        "Thank you for your payment, your order is being processed.",
        "Please let me know when you are available for a call.",
        "The package has been delivered to your address.",
        "Reminder: your gym class starts at 6 PM.",
        "Your subscription renewal is complete.",
        "Dinner plans are set for Saturday at 8 PM.",
        "Happy anniversary! Wishing you all the best.",
    ]

    if data["label"].eq("safe").sum() < max(10, data["label"].eq("spam").sum()):
        extra = pd.DataFrame({"label": ["safe"] * len(safe_examples), "message": safe_examples})
        data = pd.concat([data, extra], ignore_index=True)

    data["cleaned"] = data["message"].apply(preprocess)

    vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), min_df=1)
    X = vectorizer.fit_transform(data["cleaned"])
    model = LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear")
    model.fit(X, data["label"])

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    print(f"[train.py] Saved detector model to {MODEL_PATH}")
    print(f"[train.py] Saved vectorizer to {VECTORIZER_PATH}")


def download_kaggle_dataset():
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except (Exception, SystemExit) as error:
        print(f"[train.py] Kaggle API could not be initialized: {error}")
        print("[train.py] Skipping Kaggle download and using local data only.")
        return

    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        try:
            api = KaggleApi()
            api.authenticate()
            print("[train.py] Downloading Kaggle SMS spam dataset...")
            api.dataset_download_files(
                "uciml/sms-spam-collection-dataset",
                path=DATA_DIR,
                unzip=True,
                quiet=True,
            )
            print("[train.py] Kaggle dataset downloaded to dataset/.")
        except SystemExit as exit_error:
            print(f"[train.py] Kaggle authentication failed or API command exited: {exit_error}")
            print("[train.py] Proceeding with available local training data.")
        except Exception as error:
            print(f"[train.py] Kaggle download failed: {error}")
            print("[train.py] Proceeding with available local training data.")
    else:
        print("[train.py] KAGGLE_USERNAME or KAGGLE_KEY is not set. Proceeding with available local training data.")


if __name__ == "__main__":
    nltk.download("stopwords", quiet=True)
    download_kaggle_dataset()
    build_detector_model()
    build_chatbot_knowledge_base()
    print("[train.py] Training complete. The scam detector and chatbot knowledge base are ready.")
