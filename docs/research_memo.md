# Research Memo: Rules vs Machine Learning in Transaction Monitoring

**To:** Risk & Compliance Lead, [fictional client]
**From:** Aditya Ranjan
**Date:** 2 October 2026

## 1. Question
Should the client rely on rule-based controls, a machine-learning model, or both to
catch payment fraud?

## 2. What the project showed
I tested five SQL rule-based controls against 2,770,409 TRANSFER/CASH_OUT transactions,
8,213 of them actual fraud. Results varied a lot. C3 (destination balance check) and C4
(transfer-then-cashout) were the two solid ones — each caught about half the fraud at
65-70% precision on the full dataset. The rest were weak. C2 (account drained) caught 97.55% of fraud, but
precision was 0.67%: basically 99 out of 100 alerts it raises are false alarms. C1
(high-value transfer) and C5 (balance mismatch) were worse still. C5 flagged 2.49
million transactions — more than any other control — and caught almost no real fraud
(0.55% recall). I also hand-checked a stratified sample of 25 flagged transactions (5 per control): 7 were
actual fraud, 4 of 5 for C3 and 3 of 5 for C4, and none for C1, C2 or C5.

On the model side, logistic regression got 97.16% recall at 52.16% precision — but that
was measured on its test window (step ≥ 600), where fraud is 3.71% of transactions, far
higher than the 0.13% baseline the rule-based controls were tested on. When I re-ran C3
and C4 on that same test window for a fair comparison, their precision came out to 100%
and 98.65% — both well above logistic regression's 52.16%, at roughly half the recall.
So logistic regression's precision edge holds against the weak rules (C1, C2, C5), but
not against C3/C4, this project's two defensible controls, once measured on equal
footing. A random forest model scored almost perfectly, 99.94% recall and 100% precision, but I
don't trust that number. It comes from a leak in the PaySim data: the simulator zeroes
out an account's balance as part of generating fraud, and the model just learns to spot
that pattern instead of anything to do with fraud itself. It's a warning about trusting
a model that looks too good, not a result worth deploying.

## 3. Rules vs ML: trade-offs

| | Rule-based controls | ML models |
|---|---|---|
| Explainability to auditors/regulators | A rule is a plain condition anyone can read — "balance mismatch over X" | Logistic regression is still readable. Tree models like random forest aren't — FREE-AI flags this as a real problem, since a black-box call is hard to investigate when it's wrong |
| Maintenance | Easy to write, but thresholds go stale — my C1 threshold test showed precision/recall shift a lot depending on where you set the cutoff | Needs retraining as fraud patterns change. FREE-AI warns model performance can drift, missing new fraud or flagging good transactions |
| Catching new fraud | Weak — a rule only catches what it's written to catch | Stronger in theory, if trained on clean data without leaks |
| False positives / workload | Can get bad fast for the weak rules (C1, C2, C5) — but C3/C4 are actually tighter than the model: 100%/98.65% precision vs. logistic regression's 52.16%, measured on the same population | Trades precision for extra recall (97% vs. ~50% for C3/C4) — not simply "less noise," since the best rules beat it on precision when compared fairly |
| Data needs | Just the fields the rule checks | Needs a solid labelled fraud history, real volume, and care about leakage |

## 4. Regulatory expectations
RBI's FAQ on the Master Directions on Fraud Risk Management spells out what has to
happen once fraud is suspected, no matter how it got flagged: report it to law
enforcement, and for anything ₹1 lakh or more, that reporting is mandatory. It also says
classifying someone as fraudulent — which has real civil consequences for them — has to
go through a fair process, and it's the Board that decides which cases reach the fraud
monitoring committee and how often they get reviewed. So a control's job doesn't stop at
raising a flag; whatever happens after has to hold up to scrutiny, and that's much harder
if nobody can explain why the flag was raised.

RBI's FREE-AI report (August 2025) goes straight at this. It names fraud detection
specifically: AI can spot suspicious transactions, but it can just as easily flag
legitimate ones or miss real fraud as its performance drifts — which is more or less
what the random forest result in this project shows. Its main point is that
explainability needs to be built in from the start, not bolted on later, with
institutions checking outcomes stay fair, under a Board-approved AI policy with clear
ownership and regular audits.

## 5. Recommendation
Keep C3 and C4 as the main automated controls — they're explainable, and their
precision/recall (65-70% / ~50% on the full dataset) is something you could defend in an
audit, which matters given RBI's fair-process requirement for fraud classification. C4 has
no account link between the transfer and the cash-out, so a few of its matches are
coincidental; fix that before relying on it. Drop or rework
C5; it generates the most review work (2.49M flags) for almost nothing in return. Use
logistic regression to prioritise alerts, not to replace the rules outright — it adds
recall without the explainability problem that comes with tree ensembles, which lines up
with what FREE-AI asks for. Document every threshold and model assumption, put any model
under a Board-level AI policy with regular audits as FREE-AI recommends, and treat
unusually high model scores — like the random forest result here — as something to
investigate for leakage or drift, not as a green light to ship it.

## Sources
1. Reserve Bank of India, FAQs on *Master Directions on Fraud Risk Management in
   Commercial Banks (including Regional Rural Banks) and All India Financial
   Institutions, 2024*. https://www.rbi.org.in/commonman/Upload/English/FAQs/PDFs/RISK22042025.pdf
2. Reserve Bank of India, *Framework for Responsible and Ethical Enablement of
   Artificial Intelligence (FREE-AI)*, August 2025.
   https://rbidocs.rbi.org.in/rdocs/PublicationReport/Pdfs/FREEAIR130820250A24FF2D4578453F824C72ED9F5D5851.PDF