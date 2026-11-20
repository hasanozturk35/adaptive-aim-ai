"""
Train multiple classifiers on `data/training_shots.csv`.

What this script does:
- Loads `data/training_shots.csv` produced by the game logger.
- Extracts numeric features from each shot (player/aim/target geometry and AI state).
- Encodes the target label (`hit` -> 1, `miss` -> 0).
- Splits into train/test sets and scales features.
- Trains four models:
    - Logistic Regression (baseline)
    - Random Forest Classifier
    - Support Vector Machine (RBF kernel)
    - Polynomial Logistic Regression (PolynomialFeatures + LogisticRegression)
- Evaluates each model on the test set with accuracy, precision, recall, f1, and ROC AUC.
- Saves trained models to `models/` using joblib.

Usage:
    python train.py

Note: ensure `requirements.txt` includes scikit-learn and joblib; install with
    pip install -r requirements.txt

"""

import os
import csv
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import json


CSV_PATH = os.path.join("data", "training_shots.csv")
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLS = [
    "player_x",
    "player_y",
    "aim_x",
    "aim_y",
    "aim_dx",
    "aim_dy",
    "aim_angle_deg",
    "aim_distance",
    "target_x_at_shot",
    "target_y_at_shot",
    "target_speed",
    "target_difficulty",
    "manual_aim_mode",
]

LABEL_COL = "result"  # expects 'hit' or 'miss'


def load_data(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def prepare_xy(rows):
    X = []
    y = []
    for r in rows:
        # Skip malformed rows
        if LABEL_COL not in r or r[LABEL_COL] == "":
            continue
        try:
            features = [float(r.get(c, 0.0)) for c in FEATURE_COLS]
        except Exception:
            continue
        label = 1 if r[LABEL_COL].lower().strip() == 'hit' else 0
        X.append(features)
        y.append(label)
    return np.array(X), np.array(y)


def evaluate_model(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    probs = None
    try:
        probs = model.predict_proba(X_test)[:, 1]
    except Exception:
        try:
            probs = model.decision_function(X_test)
        except Exception:
            probs = None
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, probs) if probs is not None else float('nan')
    except Exception:
        auc = float('nan')
    print(f"{name}: acc={acc:.3f} prec={prec:.3f} rec={rec:.3f} f1={f1:.3f} auc={auc:.3f}")
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, "auc": auc}


def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        return

    rows = load_data(CSV_PATH)
    X, y = prepare_xy(rows)
    if len(y) < 10:
        print("Not enough samples to train (need >=10). Rows:", len(y))
        return

    # use a single held-out split for all candidates
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    metrics = {}

    # helper to save model dict to MODEL_DIR with given filename
    def save_model_dict(fn, model_dict):
        path = os.path.join(MODEL_DIR, fn)
        joblib.dump(model_dict, path)
        return path

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, class_weight='balanced')
    lr.fit(X_train_s, y_train)
    m_lr = evaluate_model('logistic.joblib', lr, X_test_s, y_test)
    metrics['logistic.joblib'] = m_lr
    save_model_dict('logistic.joblib', {'model': lr, 'scaler': scaler})

    # Random Forest
    rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    rf.fit(X_train, y_train)
    m_rf = evaluate_model('random_forest.joblib', rf, X_test, y_test)
    metrics['random_forest.joblib'] = m_rf
    save_model_dict('random_forest.joblib', {'model': rf, 'scaler': None})

    # SVM (RBF)
    svc = SVC(kernel='rbf', probability=True, class_weight='balanced')
    svc.fit(X_train_s, y_train)
    m_svc = evaluate_model('svm_rbf.joblib', svc, X_test_s, y_test)
    metrics['svm_rbf.joblib'] = m_svc
    save_model_dict('svm_rbf.joblib', {'model': svc, 'scaler': scaler})

    # Polynomial features + Logistic Regression
    poly = PolynomialFeatures(degree=2, include_bias=False)
    X_train_p = poly.fit_transform(X_train_s)
    X_test_p = poly.transform(X_test_s)
    lr_poly = LogisticRegression(max_iter=2000, class_weight='balanced')
    lr_poly.fit(X_train_p, y_train)
    m_poly = evaluate_model('poly_logistic.joblib', lr_poly, X_test_p, y_test)
    metrics['poly_logistic.joblib'] = m_poly
    save_model_dict('poly_logistic.joblib', {'model': lr_poly, 'scaler': scaler, 'poly': poly})

    # write metrics json
    metrics_path = os.path.join(MODEL_DIR, 'metrics.json')
    with open(metrics_path, 'w', encoding='utf-8') as mf:
        json.dump(metrics, mf, indent=2)

    # choose best by primary=f1, tie-breaker=accuracy
    best_file = None
    best_f1 = -1.0
    best_acc = -1.0
    for fn, m in metrics.items():
        f1 = float(m.get('f1', 0.0) or 0.0)
        acc = float(m.get('accuracy', 0.0) or 0.0)
        if f1 > best_f1 or (f1 == best_f1 and acc > best_acc):
            best_f1 = f1
            best_acc = acc
            best_file = fn

    if best_file is not None:
        # save best_model.joblib (re-save the model dict under this name)
        best_src = os.path.join(MODEL_DIR, best_file)
        best_dst = os.path.join(MODEL_DIR, 'best_model.joblib')
        try:
            # load and re-dump to ensure consistency
            md = joblib.load(best_src)
            joblib.dump(md, best_dst)
        except Exception:
            # fallback: copy file bytes
            import shutil
            shutil.copyfile(best_src, best_dst)

        # write best_model.json
        best_info = {
            'best_file': best_file,
            'metric': 'f1',
            'f1': best_f1,
            'accuracy': best_acc,
            'n_test': int(len(y_test)),
        }
        with open(os.path.join(MODEL_DIR, 'best_model.json'), 'w', encoding='utf-8') as bf:
            json.dump(best_info, bf, indent=2)

    print('Models saved in', MODEL_DIR)


if __name__ == '__main__':
    main()
