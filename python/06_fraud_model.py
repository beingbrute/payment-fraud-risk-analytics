"""
06_fraud_model.py | Payment Transaction Controls & Fraud Risk Analytics

Trains two simple, explainable fraud models on the PaySim data and compares
them with the rule-based controls.

Usage:  python 06_fraud_model.py --csv gold_transfer_cashout.csv
        (the Databricks export from 05_controls.sql) or the raw PaySim CSV
Dependencies: pandas, numpy, scikit-learn

Design choices (covered in the README and worth bringing up in interviews):
- Only TRANSFER and CASH_OUT rows are modelled: in PaySim, fraud occurs only
  in these two types, so other types would add rows but no signal.
- A time-based split (training on earlier steps, testing on later ones) was
  used instead of a random split, since real monitoring always predicts the
  future rather than the past.
- Accuracy isn't reported as the headline metric: fraud is well under 1% of
  rows, so predicting "no fraud" for everything would be >99% accurate and
  useless. Precision, recall and PR-AUC are reported instead.
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, classification_report,
                             confusion_matrix)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SPLIT_STEP = 600  # training on steps < 600, testing on steps >= 600 (last ~6 days)

COLS = {
    "oldbalanceOrg": "oldbalance_orig", "newbalanceOrig": "newbalance_orig",
    "oldbalanceDest": "oldbalance_dest", "newbalanceDest": "newbalance_dest",
    "nameOrig": "orig_account", "nameDest": "dest_account",
    "isFraud": "is_fraud", "isFlaggedFraud": "is_flagged_fraud",
}


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path).rename(columns=COLS)
    print(f"Rows loaded: {len(df):,} | frauds: {int(df.is_fraud.sum()):,}")
    df = df[df["type"].isin(["TRANSFER", "CASH_OUT"])].copy()
    print(f"TRANSFER + CASH_OUT rows: {len(df):,} | frauds: {int(df.is_fraud.sum()):,}")
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df["is_transfer"] = (df["type"] == "TRANSFER").astype(int)
    df["hour_of_day"] = df["step"] % 24
    # Balance reconciliation gaps, mirroring the same logic as SQL checks DQ3/DQ4
    df["orig_balance_error"] = df["oldbalance_orig"] - df["amount"] - df["newbalance_orig"]
    df["dest_balance_error"] = df["oldbalance_dest"] + df["amount"] - df["newbalance_dest"]
    df["orig_drained"] = ((df["oldbalance_orig"] > 0) & (df["newbalance_orig"] == 0)).astype(int)
    df["dest_zero_both"] = ((df["oldbalance_dest"] == 0) & (df["newbalance_dest"] == 0)).astype(int)
    df["amount_to_balance"] = df["amount"] / (df["oldbalance_orig"] + 1)
    return df


FEATURES = [
    "is_transfer", "hour_of_day", "amount",
    "oldbalance_orig", "newbalance_orig", "oldbalance_dest", "newbalance_dest",
    "orig_balance_error", "dest_balance_error",
    "orig_drained", "dest_zero_both", "amount_to_balance",
]


def evaluate(name, y_true, scores, threshold=0.5):
    pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    print(f"\n=== {name} (threshold {threshold}) ===")
    print(f"PR-AUC (average precision): {average_precision_score(y_true, scores):.4f}")
    print(f"Confusion matrix -> TP {tp:,} | FP {fp:,} | FN {fn:,} | TN {tn:,}")
    print(classification_report(y_true, pred, digits=4, zero_division=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="path to the PaySim CSV")
    ap.add_argument("--out", default="model_scores_test.csv")
    args = ap.parse_args()

    df = add_features(load(args.csv))
    train, test = df[df.step < SPLIT_STEP], df[df.step >= SPLIT_STEP]
    print(f"\nTrain: {len(train):,} rows, {int(train.is_fraud.sum()):,} frauds")
    print(f"Test : {len(test):,} rows, {int(test.is_fraud.sum()):,} frauds")

    X_tr, y_tr = train[FEATURES], train["is_fraud"]
    X_te, y_te = test[FEATURES], test["is_fraud"]

    # Model 1: logistic regression, used as a simple, explainable baseline
    logit = make_pipeline(StandardScaler(),
                          LogisticRegression(class_weight="balanced", max_iter=1000))
    logit.fit(X_tr, y_tr)
    logit_scores = logit.predict_proba(X_te)[:, 1]
    evaluate("Logistic regression", y_te, logit_scores)

    # Model 2: random forest, included to capture non-linear patterns
    rf = RandomForestClassifier(n_estimators=100, max_depth=10,
                                class_weight="balanced_subsample",
                                n_jobs=-1, random_state=42)
    rf.fit(X_tr, y_tr)
    rf_scores = rf.predict_proba(X_te)[:, 1]
    evaluate("Random forest", y_te, rf_scores)

    print("\nRandom forest feature importance:")
    imp = pd.Series(rf.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print(imp.round(4).to_string())

    # Test-period scores exported here for the Power BI model-performance page
    out = test[["step", "type", "amount", "orig_account", "dest_account", "is_fraud"]].copy()
    out["logit_score"] = logit_scores.round(6)
    out["rf_score"] = rf_scores.round(6)
    out["rf_flag"] = (rf_scores >= 0.5).astype(int)
    out.to_csv(args.out, index=False)
    print(f"\nScores written to {args.out}")


if __name__ == "__main__":
    main()