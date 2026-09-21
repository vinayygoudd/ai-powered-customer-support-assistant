from pathlib import Path
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score
from .preprocessing import split_dataset

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "support_tickets.csv"
MODEL_DIR = ROOT / "models"

def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=12000, sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

def train():
    df = pd.read_csv(DATA)
    X_train, X_test, yc_train, yc_test, yp_train, yp_test = split_dataset(df)
    category = build_pipeline().fit(X_train, yc_train)
    priority = build_pipeline().fit(X_train, yp_train)
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(category, MODEL_DIR / "category_model.joblib")
    joblib.dump(priority, MODEL_DIR / "priority_model.joblib")
    version = "tfidf-logreg-v1"
    (MODEL_DIR / "model_version.txt").write_text(version, encoding="utf-8")
    print("Category accuracy:", accuracy_score(yc_test, category.predict(X_test)))
    print("Category F1:", f1_score(yc_test, category.predict(X_test), average="weighted"))
    print("Priority accuracy:", accuracy_score(yp_test, priority.predict(X_test)))
    print("Priority F1:", f1_score(yp_test, priority.predict(X_test), average="weighted"))

if __name__ == "__main__":
    train()
