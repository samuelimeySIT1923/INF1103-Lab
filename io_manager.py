import calendar
import csv
import json
import os
from typing import Any, Dict, List
import math

import pandas as pd
import plotly.express as px
import pypdf
import streamlit as st

from ai_manager import  extract_batch_standardized_transactions, allowed_categories
from data_manager import (
    columns,
    fallback_id_prefix,
    filter_records,
    get_available_month_years,
    load_audit_trail,
    load_collated_data,
    record_audit,
    save_collated_data,
    update_collated_data,
)
from logic_manager import (
    average_monthly_essential_expenses,
    emergency_fund_inadequate,
    excessive_discretionary_spending,
    high_bills_burden,
)

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
        df_display["date"] = pd.to_datetime(
            df_display["date_and_time"],
            errors="coerce",
            format="mixed"
        )
        with st.expander("Debug: Inspect transaction dates"):
            # error catch for invalid/unsupported dates
            # to make nicer as error catch in future
            invalid_dates = df_display[df_display["date"].isna()]

            st.write("Number of invalid dates:", len(invalid_dates))
            st.write("Examples of invalid date values:")
            st.dataframe(
                invalid_dates[["transaction_id", "date_and_time"]].head(20),
                hide_index=True,
            )

            df_display["transaction_amount"] = pd.to_numeric(
                df_display["transaction_amount"], errors="coerce"
            ).fillna(0.0)
            df_display = df_display.sort_values("date")

            # selectbox_list = ["All"]
            # valid_months = df_display["date"].dt.month.dropna().unique()
            # for month_num in sorted(valid_months):
            #     selectbox_list.append(calendar.month_name[int(month_num)])

            # option = st.selectbox("Month", selectbox_list)

            # if option != "All":
            #     month_idx = list(calendar.month_name).index(option)
            #     df_display = df_display[df_display["date"].dt.month == month_idx]
            
        
            st.write("Dates found in transaction data:")
            st.dataframe(
                df[["transaction_id", "date_and_time"]],
                hide_index=True,
            )

            st.write(
                "Transactions with invalid dates:",
                df_display["date"].isna().sum()
            )

        # Get all distinct months, including their years
        month_lookup = {
            f"{calendar.month_name[month]} {year}": (year, month)
            for year, month in get_available_month_years(df_display)
        }

        selectbox_list = ["All"] + list(month_lookup.keys())

        option = st.selectbox("Month", selectbox_list)

        # Filter by the exact month AND year
        if option != "All":
            selected_year, selected_month = month_lookup[option]
            df_display = filter_records(
                df_display, month=selected_month, year=selected_year
            )


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

# -------------------------------------------------------------------------------#
    # Manual Transaction Management (Add / Amend / Delete)

    all_known_categories = sorted(list(set(allowed_categories + df["category"].dropna().astype(str).tolist())))

    with st.expander(" Add, Edit, or Archive Transactions"):
        action = st.radio("Choose Action:", ["➕ Add New Transaction", "✏️ Edit / Archive Existing Transaction"], horizontal=True)

        if action == "➕ Add New Transaction":
            col_cat1, col_cat2 = st.columns(2)
            with col_cat1:
                selected_add_cat = st.selectbox(
                    "Category", 
                    options=all_known_categories + ["+ Custom Category..."],
                    key="add_cat_select"
                )
            with col_cat2:
                custom_cat_input = ""
                if selected_add_cat == "+ Custom Category...":
                    custom_cat_input = st.text_input(
                        "Enter Custom Category Name:", 
                        placeholder="e.g. Subscriptions",
                        key="add_custom_cat_input"
                    )

            with st.form("add_transaction_form"):
                col1, col2 = st.columns(2)
                with col1:
                    add_date = st.date_input("Date")
                    add_type = st.selectbox("Type", ["Outgoing", "Incoming"])
                    add_retailer = st.text_input("Retailer", value="General Merchant")
                with col2:
                    add_amount = st.number_input("Amount (S$)", min_value=0.01, step=1.0, format="%.2f")

                submit_add = st.form_submit_button("Save Transaction")

            if submit_add:
                if not add_retailer.strip():
                    st.error("Please provide a retailer name.")
                    

                elif selected_add_cat == "+ Custom Category..." and not custom_cat_input.strip():
                    st.error("Please provide a name for the custom category.")

                else:    
                    if selected_add_cat == "+ Custom Category...":
                        cat_value = custom_cat_input.strip()
                        final_add_cat = cat_value.title()
                    else:
                        final_add_cat = selected_add_cat

                    new_rec = {
                        "transaction_id": "",
                        "date_and_time": f"{add_date} 00:00:00",
                        "retailer": add_retailer.strip(),
                        "category": final_add_cat,
                        "transaction_amount": float(add_amount),
                        "transaction_type": add_type,
                    }
                    df = save_collated_data([new_rec])
                    st.success("New transaction successfully recorded!")
                    st.rerun()

        elif action == "✏️ Edit / Archive Existing Transaction":
            if df.empty:
                st.info("No records available to edit.")
            else:
                selected_id = st.selectbox(
                    "Select Transaction ID to Modify:",
                    options=df["transaction_id"].tolist()
                )

                selected_row = df[df["transaction_id"] == selected_id].iloc[0]
                old_transaction = selected_row.to_dict()
                current_cat = str(selected_row["category"]).strip().title()

                if current_cat in allowed_categories:
                    default_cat_index = allowed_categories.index(current_cat)
                else:
                    default_cat_index = len(allowed_categories)  # Point to "+ Add New Custom Category..."

        
                cat_col1, cat_col2 = st.columns(2)
                with cat_col1:
                    selected_cat_option = st.selectbox(
                        "Category",
                        options=allowed_categories + ["+ Add New Custom Category..."],
                        index=default_cat_index,
                        key=f"edit_cat_select_{selected_id}"
                    )

                custom_cat_val = ""
                is_custom = selected_cat_option == "+ Add New Custom Category..."
                confirm_new_cat = False

                with cat_col2:
                    if is_custom:
                        default_custom_text = current_cat if current_cat not in allowed_categories else ""
                        custom_cat_val = st.text_input(
                            "Enter New Custom Category:",
                            value=default_custom_text,
                            key=f"edit_custom_input_{selected_id}"
                        ).strip().title()

                        if custom_cat_val:
                            st.warning(f"⚠️ **'{custom_cat_val}'** is not in the registered list.")
                            confirm_new_cat = st.checkbox(
                                f"Confirm adding '{custom_cat_val}' as a new category",
                                key=f"confirm_cat_{selected_id}"
                            )

                    with st.form("edit_transaction_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_date_val = pd.to_datetime(selected_row["date_and_time"]).date()
                            edit_date = st.date_input("Date", value=edit_date_val)
                            edit_type = st.selectbox(
                                "Type",
                                ["Outgoing", "Incoming"],
                                index=0 if selected_row["transaction_type"] == "Outgoing" else 1
                            )
                            edit_retailer = st.text_input("Retailer", value=str(selected_row["retailer"]))
                        with col2:
                            edit_amount = st.number_input(
                                "Amount (S$)",
                                min_value=0.01,
                                value=float(selected_row["transaction_amount"]),
                                step=1.0,
                                format="%.2f"
                            )
                        col_save, col_delete = st.columns([1, 1])
                        with col_save:
                            submit_edit = st.form_submit_button("Update Transaction")
                        with col_delete:
                            submit_delete = st.form_submit_button("Archive Transaction")

                    if submit_edit:
                        if not edit_retailer.strip():
                            st.error("Please provide a retailer name.")
                            
                        # Determine final category logic
                        elif is_custom and not custom_cat_val:
                                st.error("❌ Please provide a name for the custom category.")
                                
                        elif (
                            is_custom
                            and custom_cat_val not in allowed_categories
                            and not confirm_new_cat
                        ):
                            st.error(
                                f"❌ Update blocked: '{custom_cat_val}' is not a registered category. "
                                "Please confirm adding it as a new custom category."
                            )

                        else:
                            # Determine final category only after validation passes
                            if is_custom:
                                final_cat = custom_cat_val
                            else:
                                final_cat = selected_cat_option

                            # Save updates
                            df.loc[df["transaction_id"] == selected_id, "date_and_time"] = f"{edit_date} 00:00:00"
                            df.loc[df["transaction_id"] == selected_id, "retailer"] = edit_retailer.strip()
                            df.loc[df["transaction_id"] == selected_id, "category"] = final_cat
                            df.loc[df["transaction_id"] == selected_id, "transaction_amount"] = float(edit_amount)
                            df.loc[df["transaction_id"] == selected_id, "transaction_type"] = edit_type

                            new_transaction = df[df["transaction_id"] == selected_id].iloc[0].to_dict()
                            # Save the edit to the audit trail
                            record_audit(
                                transaction_id=selected_id,
                                action="EDIT",
                                old_data=old_transaction,
                                new_data=new_transaction,
                            )

                            df = update_collated_data(df)
                            st.success(f"Transaction {selected_id} updated with category '{final_cat}'!")
                            st.rerun()

                    if submit_delete:
                        old_transaction = selected_row.to_dict()
                        record_audit(
                            transaction_id=selected_id,
                            action="ARCHIVE",
                            old_data=old_transaction,
                        )

                        # Remove it from active transactions
                        df = df[df["transaction_id"] != selected_id].copy()
                        df = update_collated_data(df)

                        st.success(f"Transaction {selected_id} archived!")
                        st.rerun()

# Displaying the Audit trail from csv
    st.subheader("Audit Trail")

    audit_df = load_audit_trail()

    if not audit_df.empty:
        st.dataframe(audit_df, hide_index=True)
    else:
        st.info("No audit records yet.")

    st.title("Recommendation")

    with st.form("Recommend"):
        current_balance = st.text_input("Current Balance:")
        monthly_income = st.text_input("Monthly Income:")
        include_misc = st.checkbox("Include Misc in discretionary spending calculation", value=False)
        submitted_rec = st.form_submit_button("Generate")

    if submitted_rec:
        if df.empty:
            st.warning("Dataframe is empty!")
        elif current_balance == "" or monthly_income == "":
            st.warning("Please fill up both fields!")
        else:
            try:
                curr_bal = float(current_balance.strip())
                m_inc = float(monthly_income.strip())

                if not math.isfinite(curr_bal) or not math.isfinite(m_inc):
                    st.error("Please enter finite numerical amounts for both fields.")
                    st.stop()

                if curr_bal < 0 or m_inc <= 0:
                    st.error(
                        "Current Balance cannot be negative, and Monthly Income must be greater than zero."
                    )
                    st.stop()

                st.success("Generating response!")

                outgoing_all = df[df["transaction_type"] == "Outgoing"].copy()

                outgoing_all["transaction_amount"] = pd.to_numeric(
                    outgoing_all["transaction_amount"],
                    errors="coerce"
                ).fillna(0)
                
                total_expenses = pd.to_numeric(
                    outgoing_all["transaction_amount"], errors="coerce"
                ).sum()

                # Filter for recommendation calculations to look at monthly recommendations.

                if option == "All":
                    st.error(
                        "Please select a specific month and year from the Month dropdown "
                        "to generate the monthly assessment."
                    )
                    st.stop()

                selected_year, selected_month = month_lookup[option]

                monthly_df = filter_records(
                    df,
                    month=selected_month,
                    year=selected_year
                )

                outgoing_all = monthly_df[
                    monthly_df["transaction_type"] == "Outgoing"
                ].copy()

                outgoing_all["transaction_amount"] = pd.to_numeric(
                    outgoing_all["transaction_amount"],
                    errors="coerce"
                ).fillna(0)

                total_expenses = outgoing_all["transaction_amount"].sum()

                # Run both business rules using only the selected month
                discretionary_alert = excessive_discretionary_spending(
                    m_inc, monthly_df, include_misc=include_misc
                )

                bills_alert = high_bills_burden(m_inc, monthly_df)

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

                avg_essentials = average_monthly_essential_expenses(df)
                st.write(f"• **Average Monthly Essential Expenses**: S$ {avg_essentials:,.2f}")

                if emergency_fund_inadequate(curr_bal, df):
                    st.warning(
                        "⚠️ **Emergency Reserve Alert**: Current balance is below "
                        "3 months of essential expenses "
                        f"(S$ {3 * avg_essentials:,.2f}). Aim to save 3-6 months of essentials."
                    )
                else:
                    st.success(
                        "✅ **Adequate Safety Net**: Emergency reserves meet recommended guidelines."
                    )
                # discretionary-spending rule
                if discretionary_alert:
                    st.warning(
                        "⚠️ **High Discretionary Spending**: "
                        "Discretionary spending exceeds 50% of monthly income."
                    )

                # the high bills rule
                if bills_alert:
                    st.warning(
                        "⚠️ **High Bills Burden**: "
                        "Bills spending exceeds 5% of monthly income."
                    )

            except ValueError:
                st.error(
                    "Please enter valid numerical amounts for Current Balance and Monthly Income."
                )