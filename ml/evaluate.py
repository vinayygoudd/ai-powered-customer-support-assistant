from pathlib import Path
import json
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix
)
from .preprocessing import split_dataset

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "support_tickets.csv"
MODEL_DIR = ROOT / "models"
OUT = ROOT / "data" / "processed"

def evaluate_model(model, X_test, y_test, baseline_label):
    pred = model.predict(X_test)
    p, r, f, _ = precision_recall_fscore_support(
        y_test, pred, average="weighted", zero_division=0
    )
    baseline = [baseline_label] * len(y_test)
    bp, br, bf, _ = precision_recall_fscore_support(
        y_test, baseline, average="weighted", zero_division=0
    )
    return {
        "model": {
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision_weighted": float(p),
            "recall_weighted": float(r),
            "f1_weighted": float(f),
            "classification_report": classification_report(
                y_test, pred, output_dict=True, zero_division=0
            ),
            "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        },
        "majority_baseline": {
            "label": baseline_label,
            "accuracy": float(accuracy_score(y_test, baseline)),
            "precision_weighted": float(bp),
            "recall_weighted": float(br),
            "f1_weighted": float(bf),
        },
    }

def evaluate():
    df = pd.read_csv(DATA)
    X_train, X_test, yc_train, yc_test, yp_train, yp_test = split_dataset(df)
    category = joblib.load(MODEL_DIR / "category_model.joblib")
    priority = joblib.load(MODEL_DIR / "priority_model.joblib")
    result = {
        "dataset_rows": int(len(df)),
        "category": evaluate_model(category, X_test, yc_test, yc_train.mode().iloc[0]),
        "priority": evaluate_model(priority, X_test, yp_test, yp_train.mode().iloc[0]),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "category": result["category"]["model"],
        "category_majority_baseline": result["category"]["majority_baseline"],
        "priority": result["priority"]["model"],
        "priority_majority_baseline": result["priority"]["majority_baseline"],
    }, indent=2))

if __name__ == "__main__":
    evaluate()
