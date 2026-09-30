import calendar
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import pypdf
import streamlit as st

from ai_manager import extract_batch_standardized_transactions


#-----------------------------------------------------------------------------------#
#Establish columns and data path for collated data

columns = [
    "transaction_id",
    "date_and_time",
    "retailer",
    "category",
    "transaction_amount",
    "transaction_type",
]

data_path = Path("data/collated_data.csv")

fallback_id_prefix = "TXN-ERR"
id_width = 5
legacy_type_map = {"Expense": "Outgoing", "Income": "Incoming"}


#-----------------------------------------------------------------------------------#
#Establish file parsing function for uploaded files

def parse_uploaded_file(uploaded_file: Any) -> List[Any]:
    """Read raw lines or dict objects from an uploaded PDF, CSV, or JSON file."""
    fname = uploaded_file.name.lower()
    items: List[Any] = []

    try:
        if fname.endswith(".csv"):
            lines = uploaded_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(lines)
            items = [dict(row) for row in reader]

        elif fname.endswith(".json"):
            content = json.loads(uploaded_file.read().decode("utf-8"))
            if isinstance(content, list):
                items.extend(content)
            else:
                items.append(content)

        elif fname.endswith(".pdf"):
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    lines = [
                        line.strip()
                        for line in text.splitlines()
                        if len(line.strip()) > 5
                    ]
                    items.extend(lines)

    except Exception as exc:
        st.error(f"Error reading file '{uploaded_file.name}': {exc}")

    return items


def assign_sequential_ids(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ids = df["transaction_id"].astype(str).str.strip()
    is_numeric = ids.str.isdigit()

    next_id = int(ids[is_numeric].astype(int).max()) + 1 if is_numeric.any() else 1

    new_ids = ids.copy()
    new_ids[is_numeric] = ids[is_numeric].astype(int).map(lambda n: f"{n:0{id_width}d}")
    for idx in df.index[~is_numeric]:
        new_ids[idx] = f"{next_id:0{id_width}d}"
        next_id += 1

    df["transaction_id"] = new_ids
    return df


#-----------------------------------------------------------------------------------#
#Establish functions to load and save collated data

def load_collated_data() -> pd.DataFrame:
    data_path.parent.mkdir(parents=True, exist_ok=True)

    if data_path.exists() and data_path.stat().st_size > 0:
        try:
            raw_df = pd.read_csv(data_path, dtype={"transaction_id": str})
            df = raw_df.copy()

            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            df = df[columns]

            df = df[~df["transaction_id"].astype(str).str.startswith(fallback_id_prefix)]
            df = df.reset_index(drop=True)

            df["transaction_type"] = df["transaction_type"].replace(legacy_type_map)

            df = assign_sequential_ids(df)

            if not df.equals(raw_df):
                df.to_csv(data_path, index=False)
            return df
        except Exception:
            return pd.DataFrame(columns=columns)

    df = pd.DataFrame(columns=columns)
    df.to_csv(data_path, index=False)
    return df


def save_collated_data(new_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Append new standardized records to the CSV and return the updated DataFrame."""
    existing_df = load_collated_data()
    new_df = pd.DataFrame(new_records, columns=columns)
    new_df["transaction_id"] = ""  # real IDs are assigned below

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df = assign_sequential_ids(combined_df)
    combined_df.to_csv(data_path, index=False)
    return combined_df


#-----------------------------------------------------------------------------------#
#Establish Streamlit page configuration and API key handling

st.set_page_config(page_title="Personal Expenditure Manager", layout="wide")

api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key:", type="password")

df = load_collated_data()

tab1, tab2 = st.tabs(["Upload", "Recommendation"])


#-----------------------------------------------------------------------------------#
#tab 1: Uploading and processing files
with tab1:
    st.title("Personal Expenditure Manager")
    st.write(
        "Upload your spendings and income records (such as bank statements) to start tracking your finances and improving your cash flow!"
    )

    with st.form("test", clear_on_submit=True):
        file_uploaded = st.file_uploader(
            "Upload",
            label_visibility="hidden",
            type=["pdf", "csv", "json"],
            accept_multiple_files=True,
        )
        submitted = st.form_submit_button("Submit")

    if submitted:
        if not file_uploaded:
            st.warning("Please upload a file before submitting!")
        elif not api_key:
            st.warning("Please enter your Gemini API key in the sidebar to process uploads!")
        else:
            raw_items = []
            for file in file_uploaded:
                raw_items.extend(parse_uploaded_file(file))

            if not raw_items:
                st.warning(
                    "No readable transactions could be extracted from the uploaded file(s)."
                )
            else:
                st.info(
                    f"Submitted {len(raw_items)} rows of raw records."
                )

                with st.spinner(f"Processing {len(raw_items)} rows of data..."):
                    standardized_records = extract_batch_standardized_transactions(
                        raw_items, api_key
                    )

                good_records = [
                    r for r in standardized_records
                    if not str(r.get("transaction_id", "")).startswith(fallback_id_prefix)
                ]
                failed_count = len(standardized_records) - len(good_records)

                if good_records:
                    df = save_collated_data(good_records)
                    st.success(
                        "File(s) successfully uploaded and standardized "
                        f"({len(good_records)} records processed)!"
                    )
                    st.dataframe(df.tail(len(good_records))[columns], hide_index=True)
                    if failed_count:
                        st.warning(
                            f"{failed_count} record(s) could not be parsed and were not saved. "
                            "Check the terminal logs for details."
                        )
                else:
                    st.error(
                        f"Gemini extraction failed for all {failed_count} records, "
                        "so nothing was saved. If the terminal shows 503 UNAVAILABLE, Gemini is "
                        "temporarily overloaded - wait a few minutes and upload again."
                    )
    st.divider()
    st.download_button(
        label="Download File (CSV)",
        data=df[columns].to_csv(index=False).encode("utf-8"),
        file_name="transactions.csv",
        mime="text/csv",
        disabled=df.empty,
    )


#-----------------------------------------------------------------------------------#
#tab 2: Displaying data, graphs, and recommendations

with tab2:
    st.title("Data & Graphs")

    if df.empty:
        st.info(
            "No transaction data available yet. "
            "Please upload statements in the 'Upload' tab."
        )
    else:
        df_display = df.copy()
        df_display["date"] = pd.to_datetime(df_display["date_and_time"], errors="coerce")
        df_display["transaction_amount"] = pd.to_numeric(
            df_display["transaction_amount"], errors="coerce"
        ).fillna(0.0)
        df_display = df_display.sort_values("date")

        selectbox_list = ["All"]
        valid_months = df_display["date"].dt.month.dropna().unique()
        for month_num in sorted(valid_months):
            selectbox_list.append(calendar.month_name[int(month_num)])

        option = st.selectbox("Month", selectbox_list)

        if option != "All":
            month_idx = list(calendar.month_name).index(option)
            df_display = df_display[df_display["date"].dt.month == month_idx]

        table_tab, bar_tab, line_tab = st.tabs(
            ["Table", "Amount Spent Per Category", "Cumulative Amount Spent Over Time"]
        )

        with table_tab:
            st.dataframe(df_display[columns], width="stretch")

        with bar_tab:
            outgoing_df = df_display[df_display["transaction_type"] == "Outgoing"]

            if not outgoing_df.empty:
                cat_summary = (
                    outgoing_df.groupby("category")["transaction_amount"]
                    .sum()
                    .reset_index()
                )
                fig_bar = px.bar(
                    cat_summary,
                    x="category",
                    y="transaction_amount",
                    title="Amount Spent Per Category (S$)",
                    labels={
                        "transaction_amount": "Total Spent ($)",
                        "category": "Category",
                    },
                    color="category",
                )
                st.plotly_chart(fig_bar, width="stretch")
            else:
                st.info("No expense data available for the selected filter.")

        with line_tab:
            outgoing_df = df_display[df_display["transaction_type"] == "Outgoing"].copy()

            if not outgoing_df.empty:
                outgoing_df["cumulative_spending"] = outgoing_df["transaction_amount"].cumsum()
                fig_line = px.line(
                    outgoing_df,
                    x="date",
                    y="cumulative_spending",
                    title="Cumulative Spending Over Time",
                    labels={"cumulative_spending": "Total Spent ($)", "date": "Date"},
                    markers=True,
                )
                st.plotly_chart(fig_line, width="stretch")
            else:
                st.info("No expense data available to calculate cumulative spending.")

    st.divider()
    st.title("Recommendation")

    with st.form("Recommend"):
        current_balance = st.text_input("Current Balance:")
        monthly_income = st.text_input("Monthly Income:")
        submitted_rec = st.form_submit_button("Generate")

    if submitted_rec:
        if df.empty:
            st.warning("Dataframe is empty!")
        elif current_balance == "" or monthly_income == "":
            st.warning("Please fill up both fields!")
        else:
            try:
                curr_bal = float(current_balance)
                m_inc = float(monthly_income)

                st.success("Generating response!")

                outgoing_all = df[df["transaction_type"] == "Outgoing"]
                total_expenses = pd.to_numeric(
                    outgoing_all["transaction_amount"], errors="coerce"
                ).sum()

                st.subheader("Assessment Summary")
                st.write(f"• **Reported Monthly Income**: S$ {m_inc:,.2f}")
                st.write(f"• **Current Balance**: S$ {curr_bal:,.2f}")
                st.write(f"• **Total Recorded Expenses**: S$ {total_expenses:,.2f}")

                if total_expenses > m_inc:
                    st.warning(
                        "⚠️ **Cash-Flow Risk**: Expenses exceed monthly income. "
                        "Consider curbing discretionary spending."
                    )
                else:
                    st.success(
                        "✅ **Healthy Cash Flow**: Spending remains within monthly income bounds."
                    )

                if curr_bal < (3 * total_expenses):
                    st.warning(
                        "⚠️ **Emergency Reserve Alert**: Current balance is below "
                        "the recommended 3-month expense threshold."
                    )
                else:
                    st.success(
                        "✅ **Adequate Safety Net**: Emergency reserves meet recommended guidelines."
                    )

            except ValueError:
                st.error(
                    "Please enter valid numerical amounts for Current Balance and Monthly Income."
                )