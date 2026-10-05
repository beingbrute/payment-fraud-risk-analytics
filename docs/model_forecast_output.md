Rows loaded: 2,770,409 | frauds: 8,213
TRANSFER + CASH_OUT rows: 2,770,409 | frauds: 8,213

Train: 2,726,841 rows, 6,595 frauds
Test : 43,568 rows, 1,618 frauds

=== Logistic regression (threshold 0.5) ===
PR-AUC (average precision): 0.9588
Confusion matrix -> TP 1,572 | FP 1,442 | FN 46 | TN 40,508
              precision    recall  f1-score   support

           0     0.9989    0.9656    0.9820     41950
           1     0.5216    0.9716    0.6788      1618

    accuracy                         0.9658     43568
   macro avg     0.7602    0.9686    0.8304     43568
weighted avg     0.9811    0.9658    0.9707     43568


=== Random forest (threshold 0.5) ===
PR-AUC (average precision): 1.0000
Confusion matrix -> TP 1,617 | FP 0 | FN 1 | TN 41,950
              precision    recall  f1-score   support

           0     1.0000    1.0000    1.0000     41950
           1     1.0000    0.9994    0.9997      1618

    accuracy                         1.0000     43568
   macro avg     1.0000    0.9997    0.9998     43568
weighted avg     1.0000    1.0000    1.0000     43568


Random forest feature importance:
orig_balance_error    0.3634
amount_to_balance     0.2521
orig_drained          0.1003
oldbalance_orig       0.0951
dest_zero_both        0.0593
newbalance_orig       0.0424
newbalance_dest       0.0270
hour_of_day           0.0164
oldbalance_dest       0.0163
dest_balance_error    0.0137
amount                0.0116
is_transfer           0.0024

Scores written to model_scores_test.csv


Interpretation:
The random forest's near-perfect score (PR-AUC 1.0, 0 false positives, only 1 missed
fraud) is not a sign of a great model — it's a sign of data leakage. Its top features
(orig_balance_error, amount_to_balance, orig_drained) are the same balance fields that
the earlier DQ3/DQ5 checks showed are driven by a PaySim simulator artifact: the simulator
reliably drains the origin account to exactly 0 on fraudulent transactions, which gives
the model an almost perfect "fingerprint" of fraud that has nothing to do with real
fraud behavior. On real transaction data, balances would not behave this cleanly, so
this result would not hold up.

Logistic regression's lower precision (52%) is the more trustworthy number to quote,
even though it likely also benefits from the same leaky features to some degree.



## Forecast (07_forecast.py)

Series: txns, steps 1–743 (743 hours)
Back-test MAE, seasonal naive: 463.38
Back-test MAE, regression   : 1,249.19
Chosen method: seasonal naive (model did not beat it)

Forecast written to forecast_next_24h.csv, back-test to forecast_backtest.csv

Sample of next 24h forecast:
 step  hour_of_day  forecast_txns         method
  744            0           10.0 seasonal_naive
  745            1            4.0 seasonal_naive
  746            2           10.0 seasonal_naive
  750            6           22.0 seasonal_naive
  754           10           28.0 seasonal_naive
  765           21           22.0 seasonal_naive

Interpretation:
Seasonal-naive forecasting (repeating the same hour-of-day pattern from the prior
cycle) outperformed a regression model on the back-test (MAE 463 vs 1,249), so
seasonal naive was used for the final 24-hour forecast. This means transaction
volume in this data follows a strong, repeating hourly pattern rather than a trend
a regression could capture. In forecasting practice, seasonal naive is the standard
baseline a model is expected to beat — here it didn't, so using the simpler,
better-performing method was the right call rather than defaulting to the
fancier-sounding one.