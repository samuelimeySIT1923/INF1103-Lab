import pandas as pd

#Cash-flow Risk	Projected net cash flow for next 30 days < S$0
def cashflow_risk_rule(df, planned_expenses=0):
    df = df.copy()
    df['date_and_time'] = pd.to_datetime(df['date_and_time'])
    latest_date = df['date_and_time'].max()
    last_30_days = df[df['date_and_time'] > latest_date - pd.Timedelta(days=30)]
    inflow = last_30_days[last_30_days['transaction_type'] == 'Incoming']['transaction_amount'].sum()
    outflow = last_30_days[last_30_days['transaction_type'] == 'Outgoing']['transaction_amount'].sum()
    projected_net_cashflow = inflow - outflow - planned_expenses
    print(projected_net_cashflow)
    if projected_net_cashflow < 0:
        return True
    else:
        return False


#High Debt Burden	Total Monthly Debt repayments > 30% of monthly income	Student loans/debts limiting savings and increases stress	Advice refinancing or reaching out to financial assistance.



#Emergency-fund inadequacy	Savings < 3 x Saverage monthly essential expenses	Lack of safety net, face risk if there is no inflow of cash.	Advice to save 3-6 months of essentials as emergency funds.


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
def excessive_spending_rule(income,df):
    cumulative_amount_spent = 0
    for i in df['Category'].unique():
        filtered_df = df[df['Category'] == i]
        amt_spent = filtered_df["Amount"].sum()
        if i not in ['Food','Transport','Bills']:
            cumulative_amount_spent += amt_spent
    print(cumulative_amount_spent)
    if cumulative_amount_spent > (income*0.5):
        return True
    else:
        return False

#Subscription Creep	Recurring subscriptions > 5% of income	Subscriptions fees adding up financial drain	Advice on cutting unnecessary subscriptions


#High Savings (Stagnant)	Savings [left in bank] > 80% of income 	Warning of limited financial growth	Advice reaching out to financial advisers / safer investment options (eg ETFs)
