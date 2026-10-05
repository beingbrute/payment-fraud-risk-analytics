"""
07_forecast.py | Payment Transaction Controls & Fraud Risk Analytics

Forecasts hourly fraud count (or transaction volume) for the next 24 steps (1 step = 1 hour).

Usage:  python 07_forecast.py --csv gold_hourly_summary.csv            (Databricks export)
    or: python 07_forecast.py --csv paysim.csv --raw                   (raw PaySim file)
Optional: --target frauds  (forecasts fraud count instead of transaction count)

Method (kept simple and explainable):
- Baseline: seasonal naive, i.e. "same hour yesterday" (the value 24 steps ago).
- Model: linear regression on hour-of-day (one-hot), a linear trend, and the
  value 24 steps ago (lag-24).
- Back-tested on the last 24 steps (hold-out). The model is kept only if it beats
  the baseline on MAE, then refit on all data to forecast the next 24 steps.
Limitation worth stating: PaySim covers only ~31 days of simulated time, and
activity is uneven across the month, so this is a short, illustrative forecast.
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

H = 24  # forecast horizon and seasonal period (hours)


def load_series(path, raw, target):
    if raw:
        df = pd.read_csv(path, usecols=["step", "isFraud"])
        g = df.groupby("step").agg(txns=("step", "size"), frauds=("isFraud", "sum"))
    else:
        g = pd.read_csv(path).set_index("step")
    # Missing hours are filled with 0 so the series stays continuous
    full = pd.RangeIndex(g.index.min(), g.index.max() + 1, name="step")
    return g.reindex(full, fill_value=0)[target].astype(float)


def features(steps, series_for_lag):
    X = pd.DataFrame(index=steps)
    X["trend"] = steps
    hour = steps % 24
    for h in range(24):
        X[f"h{h}"] = (hour == h).astype(int)
    X["lag24"] = series_for_lag.reindex(steps - H).to_numpy()
    return X


def fit_predict(train, horizon_steps):
    idx = train.index[H:]                         # rows that have a lag-24 value
    model = LinearRegression().fit(features(idx, train), train.loc[idx])
    # For the forecast horizon, lag-24 comes from the last 24 observed hours
    X_f = features(horizon_steps, train)
    return np.clip(model.predict(X_f), 0, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--raw", action="store_true", help="input is the raw PaySim CSV")
    ap.add_argument("--target", default="txns", choices=["txns", "frauds"])
    ap.add_argument("--out", default="forecast_next_24h.csv")
    args = ap.parse_args()

    y = load_series(args.csv, args.raw, args.target)
    print(f"Series: {args.target}, steps {y.index.min()}–{y.index.max()} ({len(y)} hours)")

    # 1) Back-test on the last 24 hours
    train, test = y.iloc[:-H], y.iloc[-H:]
    naive = y.shift(H).loc[test.index]
    pred = np.round(fit_predict(train, test.index), 1)
    mae_naive = mean_absolute_error(test, naive)
    mae_model = mean_absolute_error(test, pred)
    print(f"Back-test MAE, seasonal naive: {mae_naive:,.2f}")
    print(f"Back-test MAE, regression   : {mae_model:,.2f}")
    use_model = mae_model < mae_naive
    print("Chosen method:", "regression" if use_model else "seasonal naive (model did not beat it)")

    # 2) Forecast the next 24 hours with the chosen method
    future = pd.RangeIndex(y.index.max() + 1, y.index.max() + 1 + H, name="step")
    if use_model:
        fc = fit_predict(y, future)
    else:
        fc = y.iloc[-H:].to_numpy()
    out = pd.DataFrame({"step": future, "hour_of_day": future % 24,
                        f"forecast_{args.target}": np.round(fc, 1),
                        "method": "regression" if use_model else "seasonal_naive"})
    back = pd.DataFrame({"step": test.index, "actual": test.to_numpy(),
                         "seasonal_naive": naive.to_numpy(), "regression": pred})
    out.to_csv(args.out, index=False)
    back.to_csv("forecast_backtest.csv", index=False)
    print(f"\nForecast written to {args.out}, back-test to forecast_backtest.csv")
    print(out.head(24).to_string(index=False))


if __name__ == "__main__":
    main()