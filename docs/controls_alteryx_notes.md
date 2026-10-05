# Controls and Alteryx Reconciliation Notes

## Control effectiveness (from Databricks SQL)
| Control | Flagged | Frauds caught | Precision | Recall |
|---|---|---|---|---|
| C2 – account drained | 1,188,074 | 8,012 | 0.67% | 97.55% |
| C4 – transfer→cashout (fixed) | 6,306 | 4,078 | 64.67% | 49.65% |
| C3 – dest no balance movement | 5,776 | 4,070 | 70.46% | 49.56% |
| C1 – high-value transfer | 409,110 | 2,740 | 0.67% | 33.36% |
| C5 – orig balance mismatch | 2,488,652 | 45 | 0.00% | 0.55% |

Combined, the five controls flag 2,502,462 transactions and catch 8,196 of 8,213 frauds
(99.8% recall). The 17 frauds missed by all controls (all CASH_OUT, ~$42k) became the
target the ML model was built to address.

## Alteryx reconciliation (C1, C2 rebuilt in Alteryx Designer)
| Control | SQL flagged | Alteryx flagged | SQL frauds caught | Alteryx frauds caught | Match? |
|---|---|---|---|---|---|
| C1 | 409,110 | 409,110 | 2,740 | 2,740 | Yes |
| C2 | 1,188,074 | 1,188,074 | 8,012 | 8,012 | Yes |

Both controls reconciled exactly between SQL and Alteryx, with no discrepancy found.

## C4 debugging note
The original C4 rule (chaining through orig_account = dest_account) returned 0 matches.
Investigating further showed the account-linkage itself worked (572 candidate pairs
existed), but step/amount gaps were essentially random, meaning true "transfer then
same-account cashout" chains don't actually show up this way in PaySim. An amount+timing
match tested on fraud-only rows (4,308 matched pairs) confirmed the pattern was real, so
C4 was rebuilt to match on amount and adjacent step without requiring the same account
chain. The fixed version flags 6,306 transactions at 64.67% precision and 49.65% recall.