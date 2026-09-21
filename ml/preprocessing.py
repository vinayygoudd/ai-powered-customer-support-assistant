import re
import pandas as pd
from sklearn.model_selection import train_test_split

REQUIRED_COLUMNS = ["message", "category", "priority"]

def normalize_text(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_dataset(df):
    work = df.copy()
    missing = work[REQUIRED_COLUMNS].isna().any(axis=1)
    work = work.loc[~missing].copy()
    work["message"] = work["message"].map(normalize_text)
    work = work[work["message"].str.len() > 0]
    work = work.drop_duplicates(subset=["message", "category", "priority"]).reset_index(drop=True)
    return work

def split_dataset(df, test_size=0.2, random_state=42):
    clean = clean_dataset(df)
    X = clean["message"]
    y_category = clean["category"]
    y_priority = clean["priority"]
    X_train, X_test, yc_train, yc_test, yp_train, yp_test = train_test_split(
        X, y_category, y_priority, test_size=test_size, random_state=random_state, stratify=y_category
    )
    return X_train, X_test, yc_train, yc_test, yp_train, yp_test
