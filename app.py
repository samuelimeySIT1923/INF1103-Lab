import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from pathlib import Path

# Reading csv (can replace)
if Path('data/collated_data.csv'):
    df = pd.read_csv('data/collated_data.csv')
else:
    df = pd.to_csv('data/collate_data.csv',index=False)


tab1, tab2 = st.tabs(['Upload','Recommendation'])

with tab1:
    with st.form("test",clear_on_submit=True):
        # User uploaded file for function
        file_uploaded = st.file_uploader("Upload",label_visibility='hidden',type=['pdf','jpg','png','csv'],accept_multiple_files=True)
        submitted = st.form_submit_button("Submit")

    if submitted:
        if file_uploaded != []:
            st.success(f"File(s) sucessfully uploaded")
            # Place function to upload LLM prompt

        else:
            st.warning(f"Please upload a file before submitting!")

with tab2:
    st.title("Data & Graphs",)
    table_tab, bar_tab, line_tab = st.tabs(['Table','Amount Spent Per Category','Cumulative Amount Spent Over Time'])

    # Appending months in dataframe to selectbox
    selectbox_list = ['All']
    df['date'] = pd.to_datetime(df['date'],format='%d/%m/%y')
    df = df.sort_values('date')
    for i in df['date'].dt.month.unique():
        selectbox_list.append(calendar.month_name[i])
    option = st.selectbox(
        'Month',
        selectbox_list
    )
    if option != 'All':
        df = df[df['date'].dt.month == list(calendar.month_name).index(option)]

    # Table of data
    with table_tab:
        st.dataframe(df)
    # Amount spent by category bar chart
    with bar_tab:
        st.bar_chart(
            df,
            x='category',
            y='amount',
            color='primary'
        )
    # Cumulative Spending over Time graph
    with line_tab:
        df['cumulative_spending'] = df['amount'].cumsum()
        fig = px.line(
            df, 
            x='date', 
            y='cumulative_spending',
            title='Cumulative Spending Over Time',
            labels={'cumulative_spending': 'Total Spent ($)', 'date': 'Date'}
        )
        st.plotly_chart(fig)

    st.title("Recommendation")

    with st.form("Recommend"):
        # Variables for function
        current_balance = st.text_input("Current Balance:")
        monthly_income = st.text_input("Monthly Income:")
        submitted = st.form_submit_button("Generate")
        if submitted:
            if df.empty:
                st.warning(f"Dataframe is empty!")
            elif current_balance == '' or monthly_income == '':
                st.warning(f"Please fill up both fields!")
            else:
                # Place generate recommendation function here

                st.success(f"Generating response!")
