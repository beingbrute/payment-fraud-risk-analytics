# Data Handling Note

## Data source
- Dataset: PaySim (synthetic, public, Kaggle). Downloaded on 28-09-2026.
- Contains no real customers, but was still handled as if it were sensitive, as practice
  for good habits.

## What was protected
| Field | Treatment | Layer |
|---|---|---|
| nameOrig (sending account) | Salted SHA-256 hash → `orig_account` | Silver |
| nameDest (receiving account) | Salted SHA-256 hash → `dest_account` | Silver |
| Merchant indicator | Derived as `dest_is_merchant` **before** hashing | Silver |

- The salt is stored only as a notebook widget value and is **not** in GitHub.
- Hashing is deterministic: the same account always gets the same hash, so account-level joins and grouping still work. (Control C4 does not use account IDs; it matches same-amount transfers and cash-outs by timing.)
- Check performed: rows in Silver still matching a raw ID pattern = 0.

## Retention and sharing
- Raw CSV and Bronze table: kept only in the Databricks workspace. Not published.
- Published (GitHub / Tableau Public): Gold-level aggregates and hashed data only.

## Limitations
- Hashing is pseudonymisation, not anonymisation: anyone with the salt could re-link IDs.