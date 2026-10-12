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
    #print(projected_net_cashflow)
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


#Emergency-fund inadequacy	Savings < 3 x Saverage monthly essential expenses	Lack of safety net, face risk if there is no inflow of cash.	Advice to save 3-6 months of essentials as emergency funds.
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

  
#Irregular Income Flag	Income Variance > 20% month-to-month Income [Part-timers with fluctuating cash flow	Advice on flexible budgeting/financial buffers.]
from datetime import date
from decimal import Decimal
from statistics import pstdev
THRESHOLD = Decimal("0.20")

#Def 1: get curent and last 2 months, return (year, month) strings [Newest 1st]
def last_n_months(n=3):
    today = date.today() #get today's date
    base = today.year * 12 + today.month - 1 #turn date into single “months since year 0” number
    return [(y, m + 1) for y, m in (divmod(base - i, 12) for i in range(n))]
#divmod - divides number by 12 and return (quotient, remainder) which is (year,0-based month[0-11])
#(y, m + 1) - add 1 back to conver the month to 1-12 range

#Def 2: get curent and last 2 months, return MMYY strings [Newest 1st]
def monthly_inflows(rows, months):
    totals = dict.fromkeys(months, Decimal(0)) #Create "keys" for the selected month range
    for r in rows: #for each transaction
        key = (r["date_and_time"].year, r["date_and_time"].month) #Convert row's date into (year, month)
        if r["transaction_type"] == "Incoming" and key in totals: #keep rows that are incoming + matches the "keys"
            totals[key] += Decimal(str(r["amount"])) #add amount into particular month's runing total
    return totals

#Def 3: Calculate and determine variability
def main(rows):
    #get values of 
    values = list(monthly_inflows(rows, last_n_months(3)).values()) #get total incoming of each month
    avg = sum(values) / len(values) #get average incoming of each month
    spread = pstdev(values)  #calculate income [incoming] varability
    limit = avg * THRESHOLD #calculate X% of average monthly income
    print(f"Average monthly income: {avg:.2f}")
    print(f"Income std deviation:   {spread:.2f}")
    print(f"20% of average income:  {limit:.2f}")
    if avg == 0:
        print("No income recorded, so the comparison isn't meaningful.")
    elif spread > limit:
        print("<Irregular Income Flag> Income variability is MORE than 20% of average income.")
    else:
        print("Income variability is NOT more than 20% of average income.")

if __name__ == "__main__":
    main([])  #Call in real csv data {TO LINK}


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

# #Subscription Creep	Recurring subscriptions > 5% of income	Subscriptions fees adding up financial drain	Advice on cutting unnecessary subscriptions


# #High Savings (Stagnant)	Savings [left in bank] > 80% of income 	Warning of limited financial growth	Advice reaching out to financial advisers / safer investment options (eg ETFs)
