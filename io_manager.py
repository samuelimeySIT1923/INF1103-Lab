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
from data_manager import columns, fallback_id_prefix, load_collated_data, save_collated_data


MAX_FILE_SIZE_MB = 10

def validate_uploaded_files(uploaded_files: List[Any]) -> tuple[List[Any], List[str]]:
    """Separates valid files from rejected ones based on size and content."""
    valid_files = []
    errors = []

    for file in uploaded_files:
        # Check size of file
        if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            errors.append(f" '{file.name}' rejected: Exceeds {MAX_FILE_SIZE_MB}MB size limit.")
        elif file.size == 0:
            errors.append(f" '{file.name}' rejected: File is empty.")
        else:
            valid_files.append(file)

    return valid_files, errors


def validate_and_clean_record(record: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """Validates a raw transaction dictionary against required constraints without using classes."""
    # 1. Check required keys
    for key in REQUIRED_KEYS:
        if key not in record or record[key] is None or str(record[key]).strip() == "":
            return False, record, f"Missing or empty required field: '{key}'"

    # 2. Check transaction type enum
    tx_type = str(record["transaction_type"]).capitalize().strip()
    if tx_type not in ["Incoming", "Outgoing"]:
        return False, record, f"Invalid transaction type '{record['transaction_type']}' (must be 'Incoming' or 'Outgoing')"

    # 3. Validate transaction amount
    try:
        amount = float(record["transaction_amount"])
        if amount <= 0:
            return False, record, f"Amount must be greater than zero (got {amount})"
    except (ValueError, TypeError):
        return False, record, f"Amount '{record['transaction_amount']}' is not a valid number"

    # 4. Validate date format
    try:
        parsed_date = pd.to_datetime(record["date_and_time"])
        formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return False, record, f"Invalid date/time format: '{record['date_and_time']}'"

    # Cleaned record dictionary
    cleaned = {
        "transaction_id": str(record["transaction_id"]).strip(),
        "date_and_time": formatted_date,
        "transaction_type": tx_type,
        "transaction_amount": amount,
        "category": str(record["category"]).strip().title()
    }
    return True, cleaned, ""

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



with st.expander("➕ Manually Add / Correct a Transaction"):
    with st.form("manual_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Transaction Date")
            entry_type = st.selectbox("Type", ["Outgoing", "Incoming"])
            entry_cat = st.text_input("Category", value="General")
        with col2:
            entry_amount = st.number_input("Amount (S$)", min_value=0.01, step=1.0, format="%.2f")
            entry_desc = st.text_input("Description / ID Prefix", value="Manual")

        submit_manual = st.form_submit_button("Save Record")

    if submit_manual:
        # Build manual dictionary record
        manual_record = {
            "transaction_id": f"manual_{int(pd.Timestamp.now().timestamp())}",
            "date_and_time": f"{entry_date} 00:00:00",
            "transaction_type": entry_type,
            "transaction_amount": entry_amount,
            "category": entry_cat
        }
        
        # Validate using our pure function
        is_valid, cleaned_rec, err_msg = validate_and_clean_record(manual_record)
        if is_valid:
            df = save_collated_data([cleaned_rec])
            st.success("Transaction manually recorded!")
            st.rerun()
        else:
            st.error(f"Failed to add record: {err_msg}")