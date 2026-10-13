import pandas as pd

#Business Rule 1: Cash-flow Risk	Projected net cash flow for next 30 days < S$0
def cashflow_risk_rule(df, planned_expenses=0):
    df = df.copy()
    df['date_and_time'] = pd.to_datetime(df['date_and_time'])

    latest_date = df['date_and_time'].max()
    last_30_days = df[df['date_and_time'] > latest_date - pd.Timedelta(days=30)]

    inflow = last_30_days[last_30_days['transaction_type'] == 'Incoming']['transaction_amount'].sum()
    outflow = last_30_days[last_30_days['transaction_type'] == 'Outgoing']['transaction_amount'].sum()
    projected_net_cashflow = inflow - outflow - planned_expenses

    if projected_net_cashflow < 0:
        return True
    else:
        return False


#High Debt Burden	Total Monthly Debt repayments > 30% of monthly income	Student loans/debts limiting savings and increases stress	Advice refinancing or reaching out to financial assistance.
def excessive_discretionary_spending(
        monthly_income, df, include_misc=False
):
    df = df.copy()
    #convert to numbers n keep the outgoing transactions
    df["transaction_amount"]=pd.to_numeric(
        df["transaction_amount"], errors="coerce"
    ).fillna(0)
    outgoing = df[df["transaction_type"]=="Outgoing"]

    #find discretionary cats
    discretionary_categories = {"entertainment", "shopping"}
    if include_misc:
        discretionary_categories.add("misc")
    categories = outgoing["category"].astype(str).str.strip().str.lower()
    discretionary_spending = outgoing.loc[
        categories.isin(discretionary_categories),
        "transaction_amount"
    ].sum()
    if monthly_income <= 0:
        return False

    return discretionary_spending > monthly_income * 0.50

#Business Rule 2: High Bills Burden	Monthly bills > 5% of monthly income	High bills burden limits savings and increases stress	Advice to reduce bills (eg. switch telco, electricity, insurance)
def high_bills_burden(monthly_income, df):
    df = df.copy()

    df["transaction_amount"] = pd.to_numeric(
        df["transaction_amount"], errors="coerce"
    ).fillna(0)

    bills = df[
        (df["transaction_type"] == "Outgoing")
        & (df["category"].astype(str).str.strip().str.lower() == "bills")
    ]

    bills_spending = bills["transaction_amount"].sum()

    if monthly_income <= 0:
        return False

    return bills_spending > monthly_income * 0.05


#Business Rule 3: Emergency-fund inadequacy	Savings < 3 x Saverage monthly essential expenses	Lack of safety net, face risk if there is no inflow of cash.	Advice to save 3-6 months of essentials as emergency funds.
essential_categories = {"food", "groceries", "transport", "bills"}

def average_monthly_essential_expenses(df: pd.DataFrame) -> float:
    """Return the average essential spending per month, across the months that have records."""
    df = df.copy()
    df["transaction_amount"] = pd.to_numeric(
        df["transaction_amount"], errors="coerce"
    ).fillna(0)

    dates = pd.to_datetime(df["date_and_time"], errors="coerce", format="mixed")
    month_count = dates.dt.to_period("M").nunique()
    if month_count == 0:
        return 0.0

    categories = df["category"].astype(str).str.strip().str.lower()
    essentials = df[
        (df["transaction_type"] == "Outgoing")
        & categories.isin(essential_categories)
    ]

    return float(essentials["transaction_amount"].sum() / month_count)

def emergency_fund_inadequate(
        savings: float, df: pd.DataFrame, months_required: int = 3
) -> bool:
    """Flag when savings cover less than `months_required` months of essential expenses."""
    return savings < months_required * average_monthly_essential_expenses(df)

  
#Business Rule 4: Irregular Income Flag Income Variance > 20% month-to-month Income [Part-timers with fluctuating cash flow	Advice on flexible budgeting/financial buffers.]
from decimal import Decimal #pandas already imported, add if not included
THRESHOLD = 0.2 

def irregular_income(df, n_months=3):
    if df.empty: #no transaction rows = return none
        return None
    df = df.copy()     #create a copy of the data
    df["date_and_time"] = pd.to_datetime(df["date_and_time"]) #convert to real datatime values
    incoming = df[df["transaction_type"] == "Incoming"]     # keep incoming transaction types only
    last_month = df["date_and_time"].max().to_period("M") #Get the last n calendar months in the data
    months = pd.period_range(end=last_month, periods=n_months, freq="M") #3 consecutive months ending at that month built
    monthly = (
        incoming.groupby(incoming["date_and_time"].dt.to_period("M"))["transaction_amount"]
        .sum()
        .reindex(months, fill_value=0)
    )     #build a series of total incoming per month (over 3 months); sum all in month, reindex adds 0 for months with no incoming rows
    avg = monthly.mean() #get average monthly mean
    if avg == 0: #no income rows = return none
        return None
    spread = monthly.std(ddof=0)  # Find standard deviation
    return bool(spread > avg * THRESHOLD) #True = irregular, false = regular


#Business Rule 5: Excessive Discretionary Spending	Discretionary Category > 50% of income 	Overspending on non-essentials result in financial drain	Advice to reduce 
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


#Business Rule 6: Subscription Creep	Recurring subscriptions > 5% of income	Subscriptions fees adding up financial drain	Advice on cutting unnecessary subscriptions
def subscription_creep(monthly_income, df):
    df = df.copy()
    df['date_and_time'] = pd.to_datetime(df['date_and_time'])
    df['transaction_amount'] = pd.to_numeric(
        df['transaction_amount'], errors='coerce'
    ).fillna(0)

    latest_date = df['date_and_time'].max()
    last_30_days = df[df['date_and_time'] > latest_date - pd.Timedelta(days=30)]

    categories = last_30_days['category'].astype(str).str.strip().str.lower()
    subscriptions = last_30_days[
        (last_30_days['transaction_type'] == 'Outgoing')
        & categories.str.contains('subscription')
    ]
    subscription_spending = subscriptions['transaction_amount'].sum()

    if monthly_income <= 0:
        return False

    if subscription_spending > monthly_income * 0.05:
        return True
    else:
        return False


#Business Rule 7: High Savings (Stagnant)	Savings [left in bank] > 80% of income 	Warning of limited financial growth	Advice reaching out to financial advisers / safer investment options (eg ETFs)
def high_savings_stagnant(monthly_income, savings):
    if monthly_income <= 0:
        return False

    if savings > monthly_income * 0.80:
        return True
    else:
        return False