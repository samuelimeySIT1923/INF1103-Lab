#Cash-flow Risk	Projected net cash flow for next 30 days < S$0


#High Debt Burden	Total Monthly Debt repayments > 30% of monthly income	Student loans/debts limiting savings and increases stress	Advice refinancing or reaching out to financial assistance.



#Emergency-fund inadequacy	Savings < 3 x average monthly essential expenses	Lack of safety net, face risk if there is no inflow of cash.	Advice to save 3-6 months of essentials as emergency funds.


#Irregular Income Flag	Income Variance > 20% month-to-month	Part-timers with fluctuating cash flow	Advice on flexible budgeting/financial buffers.
#<Focus>
currentMMYYYY = #HOW TO GET current month and year
prev1MMYYYY = 
prev2MMYYYY = 
#call data that has inflow flag
#for MMYYYY in 3MMYYYY:
  #for day in MMYYYY
    if TransactionType.lower() == 'inflow' 
      getIncome =+ TransactionAmount
    #WIP

#Excessive DiscretionarySpending 	Discretionary Category > 50% of income 	Overspending on non-essentials result in financial drain	Advice to reduce 


#Subscription Creep	Recurring subscriptions > 5% of income	Subscriptions fees adding up financial drain	Advice on cutting unnecessary subscriptions


#High Savings (Stagnant)	Savings [left in bank] > 80% of income 	Warning of limited financial growth	Advice reaching out to financial advisers / safer investment options (eg ETFs)
