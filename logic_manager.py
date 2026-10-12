#Cash-flow Risk	Projected net cash flow for next 30 days < S$0


#High Debt Burden	Total Monthly Debt repayments > 30% of monthly income	Student loans/debts limiting savings and increases stress	Advice refinancing or reaching out to financial assistance.



#Emergency-fund inadequacy	Savings < 3 x average monthly essential expenses	Lack of safety net, face risk if there is no inflow of cash.	Advice to save 3-6 months of essentials as emergency funds.

#1. get curent and last 2 months, return MMYY [Newest 1st]
#2. for every MMYY obtained, 
# a. call every inflow within the month
# b. tabulate the sum of inflow within said month
#3. calculate variance in income in past 3 months
#4. Calculate if variance is more than 20% of average month-to-month Income


#Irregular Income Flag	Income Variance > 20% month-to-month Income [Part-timers with fluctuating cash flow	Advice on flexible budgeting/financial buffers.]
#<Focus>

from datetime import date
from decimal import Decimal
from statistics import pstdev

threshold = Decimal("0.20")

#Def 1: get curent and last 2 months, return MMYY strings [Newest 1st]
def last_n_Months(n = 3) -> list[str]:  
    today = date.today()
    year, month = today.year, today.month #unpack month and year into 2 different intgers
    keys = [] #list to collect MMYYYY Strings
    for _ in range(n):
        keys.append(f"{month:02d}{year}")
        month -= 1
        # roll back across the year boundary
        if month == 0:                 
            month, year = 12, year - 1
    return keys

#Def 2A: Get every Inflows amount recorded in given month
def get_Inflows(mainRows: list[dict], mmyyyy: str) -> list[Decimal]:
    month, year = int(mmyyyy[:2]), int(mmyyyy[2:])
    return [
        Decimal(str(row["amount"]))
        for row in mainRows
        if row["transaction_type"] == "Incoming"
        and row["date"].month == month
        and row["date"].year == year
    ]

#Def 2B: sum up all inflows by month
def sum_Inflows_By_Month(mainRows: list[dict], keys: list[str]) -> dict[str, Decimal]:
    totals = {} #get empty array
    for key in keys: #For each MMYYYY
        inflows = get_Inflows(mainRows, key)
        #get all inflows in that month
        totals[key] = sum(inflows, Decimal("0"))
        # Tabulate the sum
    return totals

#Def 3: Calculate Variability in income of past 3 months
def income_Variability(monthlytotals: dict[str, Decimal]) -> tuple[Decimal, Decimal]:
    values = list(monthlytotals.values())
    avg = sum(values, Decimal("0")) / len(values)
    spread = pstdev(values)  # population std dev; use stdev() for sample
    return spread, avg  

#Def 4: Calculate if Variability os more than 20% average monthly income
def main(mainRows: list[dict]):
    keys = last_n_Months(3) #call last 3 months
    monthlytotals = sum_Inflows_By_Month(mainRows, keys) #get total inflow of each month

    spread, avgincome = income_Variability(monthlytotals) #calculate income varability & average monthly income
    limit = avgincome * threshold #calculate 20% of average monthly income

    print(f"Average monthly income: {avgincome:.2f}")
    print(f"Income std deviation:   {spread:.2f}")
    print(f"20% of average income:  {limit:.2f}")

    if avgincome == 0:
        print("No income recorded, so the comparison isn't meaningful.")
        #if no income detected, cannot compare > exit
    elif spread > limit:
        print("<Irregular Income Flag> Income variability is MORE than 20% of average income.")
        # if variability > 20% average income =  flag
    else:
        print("Income variability is NOT more than 20% of average income.")
        # if variability <= 20% average income = No flag

if __name__ == "__main__":
    mainRows = [
        #Call in real csv data {TO LINK}
    ]
    main(mainRows)


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
