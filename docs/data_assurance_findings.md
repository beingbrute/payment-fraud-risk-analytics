1. Which check fails most often, and is it a data-quality problem or a risk signal?

The two highest-volume checks, DQ3 (sender balance mismatch, 56.6% of transactions) 
and DQ5 (amount exceeds balance, 56.6%), are data-quality artifacts, not risk signals — their fraud 
share is close to 0%. Investigating further, these failures are concentrated almost 
entirely in outgoing transaction types (CASH_OUT, PAYMENT, TRANSFER, DEBIT), while CASH_IN — where 
the origin is the party receiving money — fails only 0.002% of the time. This shows PaySim's balance 
simulation reliably tracks incoming balance changes but doesn't consistently track 
outgoing balance changes, partly because many origin accounts start with a zero 
balance the simulator never populated. I flagged this as a known limitation of the 
synthetic dataset rather than a fraud indicator.



2. Is the fraud share among exceptions much higher than the overall fraud rate?

Yes, for DQ4 specifically (receiver balance mismatch, real customer accounts only). 
The overall fraud rate in the dataset is 0.13% (8,213 of 6,362,620 transactions), but DQ4 exceptions 
have a 1.57% fraud share — about 12x higher than baseline. That makes DQ4 the one 
data-quality check that's also a meaningful risk signal, unlike DQ3/DQ5, which
 showed no fraud concentration at all.



3. What would you recommend the "client" fix at source?

The origin-balance tracking issue (DQ3/DQ5) should be fixed in the transaction-processing 
system itself — every outgoing transaction should read and write the sender's actual balance 
at time of transaction, not leave it unpopulated for new or 
low-activity accounts. Until that's fixed, DQ3/DQ5 shouldn't be used 
as fraud controls since they don't discriminate fraud from legitimate 
transactions. DQ4, on the other hand, is worth escalating as an 
active control, since it's correlated with real fraud.