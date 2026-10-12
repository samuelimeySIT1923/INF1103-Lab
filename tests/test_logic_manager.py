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