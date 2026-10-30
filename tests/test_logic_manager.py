import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import logic_manager


# Hardcoded records in the shape the AI returns, so no live API is needed
sample_ai_records = [
    {"date_and_time": "2026-08-03 12:30:00", "retailer": "NTUC FairPrice", "category": "Groceries",
     "transaction_amount": 300.0, "transaction_type": "Outgoing"},
    {"date_and_time": "2026-08-10", "retailer": "SP Group", "category": "Bills",
     "transaction_amount": 200.0, "transaction_type": "Outgoing"},
    {"date_and_time": "2026-08-20", "retailer": "Golden Village", "category": "Entertainment",
     "transaction_amount": 500.0, "transaction_type": "Outgoing"},
    {"date_and_time": "2026-09-01", "retailer": "Employer", "category": "Misc",
     "transaction_amount": 2500.0, "transaction_type": "Incoming"},
    {"date_and_time": "2026-09-05", "retailer": "Grab", "category": "Transport",
     "transaction_amount": 100.0, "transaction_type": "Outgoing"},
    {"date_and_time": "2026-09-12", "retailer": "Kopitiam", "category": "Food",
     "transaction_amount": 400.0, "transaction_type": "Outgoing"},
]


def sample_df():
    return pd.DataFrame(sample_ai_records)


def test_average_counts_only_essential_outgoing_spending():
    # Essentials: 300 + 200 in August, 100 + 400 in September = 1000 over 2 months
    assert logic_manager.average_monthly_essential_expenses(sample_df()) == 500.0


def test_average_is_zero_with_no_records():
    empty = pd.DataFrame(columns=["date_and_time", "retailer", "category",
                                  "transaction_amount", "transaction_type"])
    assert logic_manager.average_monthly_essential_expenses(empty) == 0.0


def test_average_treats_unreadable_amounts_as_zero():
    records = [dict(sample_ai_records[0], transaction_amount="not a number")] + sample_ai_records[1:]
    df = pd.DataFrame(records)
    # 300 is lost, leaving 700 over 2 months
    assert logic_manager.average_monthly_essential_expenses(df) == 350.0


def test_emergency_fund_flagged_when_savings_below_three_months():
    # Threshold is 3 x 500 = 1500
    assert logic_manager.emergency_fund_inadequate(1499.99, sample_df()) is True


def test_emergency_fund_not_flagged_at_or_above_three_months():
    assert logic_manager.emergency_fund_inadequate(1500.0, sample_df()) is False
    assert logic_manager.emergency_fund_inadequate(9000.0, sample_df()) is False


def test_emergency_fund_not_flagged_with_no_essential_spending():
    df = sample_df()
    df = df[df["category"] == "Entertainment"]
    assert logic_manager.emergency_fund_inadequate(0.0, df) is False

    

# Cash-flow risk

def test_cashflow_not_at_risk_when_income_covers_spending():
    # Latest record is 12 Sep, so the last 30 days hold 2500 in and 500 + 100 + 400 out
    assert not logic_manager.cashflow_risk_rule(sample_df())


def test_cashflow_not_at_risk_when_planned_expenses_equal_surplus():
    assert not logic_manager.cashflow_risk_rule(sample_df(), planned_expenses=1500)


def test_cashflow_at_risk_when_planned_expenses_exceed_surplus():
    assert logic_manager.cashflow_risk_rule(sample_df(), planned_expenses=1500.01)


def test_cashflow_at_risk_when_spending_exceeds_income():
    df = sample_df()
    df = df[df["transaction_type"] == "Outgoing"]
    assert logic_manager.cashflow_risk_rule(df)


def test_cashflow_handles_unreadable_dates():
    records = [dict(r, date_and_time="not a date") for r in sample_ai_records]
    assert not logic_manager.cashflow_risk_rule(pd.DataFrame(records))


# Excessive discretionary spending

def test_discretionary_flagged_when_above_half_of_income():
    # Discretionary spending is 500 (Entertainment); half of 900 is 450
    assert logic_manager.excessive_discretionary_spending(900, sample_df())


def test_discretionary_not_flagged_at_exactly_half_of_income():
    assert not logic_manager.excessive_discretionary_spending(1000, sample_df())


def test_discretionary_not_flagged_with_zero_income():
    assert not logic_manager.excessive_discretionary_spending(0, sample_df())


def test_discretionary_can_include_misc():
    records = sample_ai_records + [
        {"date_and_time": "2026-09-15", "retailer": "PayNow", "category": "Misc",
         "transaction_amount": 100.0, "transaction_type": "Outgoing"},
    ]
    df = pd.DataFrame(records)
    # 500 without Misc is not above half of 1100; 600 with Misc is
    assert not logic_manager.excessive_discretionary_spending(1100, df)
    assert logic_manager.excessive_discretionary_spending(1100, df, include_misc=True)


# High bills burden

def test_bills_burden_flagged_when_above_five_percent_of_income():
    # Bills are 200; 5% of 3999 is 199.95
    assert logic_manager.high_bills_burden(3999, sample_df())


def test_bills_burden_not_flagged_at_exactly_five_percent():
    assert not logic_manager.high_bills_burden(4000, sample_df())


def test_bills_burden_not_flagged_with_zero_income():
    assert not logic_manager.high_bills_burden(0, sample_df())


# Subscription creep

def subscription_df():
    records = sample_ai_records + [
        {"date_and_time": "2026-08-01", "retailer": "Spotify", "category": "Subscriptions",
         "transaction_amount": 500.0, "transaction_type": "Outgoing"},
        {"date_and_time": "2026-09-10 09:00:00", "retailer": "Netflix", "category": "Subscriptions",
         "transaction_amount": 20.0, "transaction_type": "Outgoing"},
    ]
    return pd.DataFrame(records)


def test_subscription_creep_flagged_when_above_five_percent_of_income():
    # Only the 20 on 10 Sep is inside the last 30 days; 5% of 399 is 19.95
    assert logic_manager.subscription_creep(399, subscription_df())


def test_subscription_creep_not_flagged_at_exactly_five_percent():
    assert not logic_manager.subscription_creep(400, subscription_df())


def test_subscription_creep_not_flagged_without_subscriptions():
    assert not logic_manager.subscription_creep(100, sample_df())


def test_subscription_creep_not_flagged_with_zero_income():
    assert not logic_manager.subscription_creep(0, subscription_df())


# High savings (stagnant)

def test_high_savings_flagged_when_above_eighty_percent_of_income():
    assert logic_manager.high_savings_stagnant(1000, 800.01)


def test_high_savings_not_flagged_at_exactly_eighty_percent():
    assert not logic_manager.high_savings_stagnant(1000, 800)


def test_high_savings_not_flagged_with_zero_income():
    assert not logic_manager.high_savings_stagnant(0, 5000)





# Excessive spending (everything outside the essential categories)

def test_excessive_spending_flagged_when_above_half_of_income():
    # Non-essential outgoing spending is 500 (Entertainment); half of 999 is 499.5
    assert logic_manager.excessive_spending_rule(999, sample_df())


def test_excessive_spending_not_flagged_at_exactly_half_of_income():
    assert not logic_manager.excessive_spending_rule(1000, sample_df())


def test_excessive_spending_ignores_incoming_and_essential_records():
    # The 2500 salary is Misc but Incoming, and Groceries/Bills/Transport/Food are essential
    df = sample_df()
    df = df[df["category"] != "Entertainment"]
    assert not logic_manager.excessive_spending_rule(1, df)


def test_excessive_spending_counts_outgoing_misc():
    records = sample_ai_records + [
        {"date_and_time": "2026-09-15", "retailer": "PayNow", "category": "Misc",
         "transaction_amount": 100.0, "transaction_type": "Outgoing"},
    ]
    df = pd.DataFrame(records)
    # 500 + 100 = 600 is above half of 1100, where the discretionary rule (500) is not
    assert logic_manager.excessive_spending_rule(1100, df)
    assert not logic_manager.excessive_discretionary_spending(1100, df)


def test_excessive_spending_not_flagged_with_zero_income():
    assert not logic_manager.excessive_spending_rule(0, sample_df())



# Irregular income

def income_df(monthly_amounts):
    records = [
        {"date_and_time": f"{month}-25", "retailer": "Employer", "category": "Misc",
         "transaction_amount": amount, "transaction_type": "Incoming"}
        for month, amount in monthly_amounts.items()
    ]
    return pd.DataFrame(records)


def test_irregular_income_flagged_when_monthly_income_varies():
    df = income_df({"2026-07": 1000.0, "2026-08": 2000.0, "2026-09": 3000.0})
    assert logic_manager.irregular_income(df)


def test_irregular_income_not_flagged_when_income_is_steady():
    df = income_df({"2026-07": 2000.0, "2026-08": 2000.0, "2026-09": 2100.0})
    assert not logic_manager.irregular_income(df)


def test_irregular_income_counts_a_missing_month_as_zero():
    # Only two of the three months in the window have income
    df = income_df({"2026-08": 2000.0, "2026-09": 2000.0})
    assert logic_manager.irregular_income(df)
    assert not logic_manager.irregular_income(df, months=2)


def test_irregular_income_ignores_months_outside_the_window():
    df = income_df({"2025-01": 9000.0, "2026-07": 2000.0, "2026-08": 2000.0, "2026-09": 2000.0})
    assert not logic_manager.irregular_income(df)


def test_irregular_income_handles_mixed_date_formats():
    # sample_df mixes "2026-08-10" and "2026-08-03 12:30:00"
    assert logic_manager.irregular_income(sample_df())


def test_irregular_income_not_flagged_without_usable_data():
    outgoing_only = [r for r in sample_ai_records if r["transaction_type"] == "Outgoing"]
    assert not logic_manager.irregular_income(pd.DataFrame(outgoing_only))

    unreadable = [dict(r, date_and_time="not a date") for r in sample_ai_records]
    assert not logic_manager.irregular_income(pd.DataFrame(unreadable))

    empty = pd.DataFrame(columns=["date_and_time", "retailer", "category",
                                  "transaction_amount", "transaction_type"])
    assert not logic_manager.irregular_income(empty)