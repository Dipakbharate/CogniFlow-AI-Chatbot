'''
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trained_model', 'intent_model.pkl')
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'intent_dataset.csv')

def train_model():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
        
    df = pd.read_csv(DATASET_PATH)
    
    # Train a simple text classification model
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LogisticRegression(C=10, max_iter=1000)
    )
    
    model.fit(df['text'], df['intent'])
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    joblib.dump(model, MODEL_PATH)
    print(f"Model trained and saved to {MODEL_PATH}")
    return model

def get_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        return train_model()

# Load the model once when the module is imported
try:
    classifier = get_model()
except Exception as e:
    print(f"Failed to load or train model: {e}")
    classifier = None

def detect_intent(user_input: str) -> str:
    """
    Predicts the intent of the user using the trained ML model.
    Intents: 'greeting', 'farewell', 'image_request', 'file_request', 'general_query', 'contextual'
    """
    if classifier is None:
        return "general_query"
        
    try:
        prediction = classifier.predict([user_input])[0]
        return prediction
    except Exception as e:
        print(f"Prediction error: {e}")
        return "general_query"
    '''
import os
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")  # non-interactive, works on Windows too
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
 
# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH   = os.path.join(BASE_DIR, "data", "trained_model", "intent_model.pkl")
DATASET_PATH = os.path.join(BASE_DIR, "data", "intent_dataset.csv")
REPORT_DIR   = os.path.join(BASE_DIR, "data", "evaluation")
 
 
# ── Training + Full Evaluation ─────────────────────────────────────────────────
def train_model():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
 
    df = pd.read_csv(DATASET_PATH)
 
    print("=" * 55)
    print("     INTENT CLASSIFIER - TRAINING REPORT")
    print("=" * 55)
    print(f"\n[DATA] Total samples: {len(df)}")
    print(f"\n[STATS] Class Distribution:")
    print(df["intent"].value_counts().to_string())
 
    X = df["text"]
    y = df["intent"]
    labels = sorted(y.unique())
 
    # ── 1. Train / Test Split (80/20) ──────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n[SPLIT] Train/Test Split:")
    print(f"   Training samples : {len(X_train)} (80%)")
    print(f"   Testing  samples : {len(X_test)} (20%)")
 
    # ── 2. Build & Train Pipeline ──────────────────────────────────────────────
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=1, lowercase=True),
        LogisticRegression(C=10, max_iter=1000, solver="lbfgs"),
    )
 
    print("\n[TRAIN] Training model...")
    model.fit(X_train, y_train)
 
    # ── 3. Cross Validation ────────────────────────────────────────────────────
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    print(f"\n[CV] 5-Fold Cross Validation:")
    print(f"   Scores : {[f'{s:.2%}' for s in cv_scores]}")
    print(f"   Mean   : {cv_scores.mean():.2%}")
    print(f"   Std    : {cv_scores.std():.4f}")
 
    # ── 4. Accuracy Score ──────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n[OK] Test Set Accuracy: {acc * 100:.2f}%")
 
    # ── 5. Classification Report ───────────────────────────────────────────────
    print(f"\n[REPORT] Classification Report (precision / recall / F1):")
    print(classification_report(y_test, y_pred, target_names=labels))
 
    # ── 6. Confusion Matrix saved as PNG ──────────────────────────────────────
    os.makedirs(REPORT_DIR, exist_ok=True)
    cm = confusion_matrix(y_test, y_pred, labels=labels)
 
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title(f"Confusion Matrix  |  Test Accuracy: {acc:.2%}", fontsize=13, pad=12)
    ax.set_xlabel("Predicted Intent", fontsize=11)
    ax.set_ylabel("Actual Intent", fontsize=11)
    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
 
    cm_path = os.path.join(REPORT_DIR, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=150)
    plt.close()
    print(f"[IMG] Confusion matrix saved -> {cm_path}")
 
    # ── 7. Save Model ──────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"[SAVE] Model saved -> {MODEL_PATH}")
    print("\n" + "=" * 55)
 
    return model
 
 
# ── Load Model ─────────────────────────────────────────────────────────────────
def get_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return train_model()
 
 
# Load once at import
try:
    classifier = get_model()
except Exception as e:
    print(f"Failed to load or train model: {e}")
    classifier = None
 
 
# ── Prediction ─────────────────────────────────────────────────────────────────
def detect_intent(user_input: str) -> str:
    """
    Predicts the intent of the user using the trained ML model.
    Intents: greeting | farewell | image_request | file_request | general_query | contextual
    """
    if classifier is None:
        return "general_query"
    try:
        return classifier.predict([user_input])[0]
    except Exception as e:
        print(f"Prediction error: {e}")
        return "general_query"
 
 
def detect_intent_with_confidence(user_input: str) -> dict:
    """
    Returns predicted intent + confidence scores for all classes.
    """
    if classifier is None:
        return {"intent": "general_query", "confidence": 0.0, "scores": {}}
    try:
        intent = classifier.predict([user_input])[0]
        probs  = classifier.predict_proba([user_input])[0]
        labels = classifier.classes_
        return {
            "intent":     intent,
            "confidence": round(float(max(probs)), 4),
            "scores":     {l: round(float(p), 4) for l, p in zip(labels, probs)},
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"intent": "general_query", "confidence": 0.0, "scores": {}}
 
 
# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Force retrain so full evaluation is printed every run
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)
 
    train_model()
 
    print("\nSmoke Test:")
    tests = [
        "hello there",
        "goodbye see you later",
        "generate an image of a dragon",
        "create a pdf report for me",
        "what is machine learning",
        "do you remember what we talked about last time",
    ]
    for text in tests:
        r = detect_intent_with_confidence(text)
        print(f"  Input  : '{text}'")
        print(f"  Intent : {r['intent']}  ({r['confidence']:.0%} confident)\n")
 