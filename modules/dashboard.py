import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import database as db
from modules import utils, stocks

def view():
    st.header("Dashboard")
    
    # Date Filter (Default to current month)
    today = date.today()
    current_month_str = today.strftime("%Y-%m")
    
    # Fetch Data
    df_tx = db.get_all_transactions()
    df_stocks = db.get_stocks()
    
    # Calculate Totals
    total_income = 0
    total_expenses = 0
    monthly_expenses = 0
    
    if not df_tx.empty:
        # Convert date to datetime
        df_tx['date'] = pd.to_datetime(df_tx['date'])
        
        total_income = df_tx[df_tx['type'] == 'Income']['amount'].sum()
        total_expenses = df_tx[df_tx['type'] == 'Expense']['amount'].sum()
        
        # Monthly Expenses
        mask = (df_tx['date'].dt.to_period('M') == current_month_str) & (df_tx['type'] == 'Expense')
        monthly_expenses = df_tx[mask]['amount'].sum()

    # Stock Value
    stock_value = 0
    if not df_stocks.empty:
        # We need current prices for accurate asset value
        # For dashboard speed, we might want to cache this or just use last known
        # For now, we'll re-calculate quickly or use buy price if fetch fails
        # To avoid slow dashboard, let's just use cost basis + simple estimate or just cost if we want speed
        # But user wants "Total Assets", so let's try to get value.
        # We can reuse the logic from stocks.py but maybe simplified.
        # For now, let's just sum the cost basis to be safe and fast, 
        # or if we want to be fancy, we call the price fetcher (might be slow).
        # Let's sum cost for now and add a note.
        stock_value = (df_stocks['buy_price'] * df_stocks['quantity']).sum() 
        # Ideally we'd fetch prices here too, but let's keep it simple for V1.
    
    # Budget
    budget = db.get_budget(current_month_str)
    if budget == 0:
        budget = 30000 # Default default
    
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Assets (Est)", utils.format_currency(total_income - total_expenses + stock_value)) # Simplified asset calc
    col2.metric("Monthly Expenses", utils.format_currency(monthly_expenses), delta=utils.format_currency(budget - monthly_expenses))
    col3.metric("Monthly Budget", utils.format_currency(budget))
    col4.metric("Stock Cost Basis", utils.format_currency(stock_value))
    
    # Budget Progress
    st.subheader("Monthly Budget Progress")
    progress = min(monthly_expenses / budget, 1.0) if budget > 0 else 0
    st.progress(progress)
    st.caption(f"Spent {utils.format_currency(monthly_expenses)} of {utils.format_currency(budget)}")
    
    # Set Budget
    with st.expander("Adjust Budget"):
        new_budget = st.number_input("Set Budget for this month", value=float(budget))
        if st.button("Update Budget"):
            db.set_budget(current_month_str, new_budget)
            st.rerun()

    # Charts
    st.subheader("Analysis")
    col1, col2 = st.columns(2)
    
    if not df_tx.empty:
        # Expense by Category
        expenses_df = df_tx[df_tx['type'] == 'Expense']
        if not expenses_df.empty:
            fig_cat = px.pie(expenses_df, values='amount', names='category', title='Expenses by Category')
            col1.plotly_chart(fig_cat, use_container_width=True)
            
            # Daily Spending Trend
            daily_spend = expenses_df.groupby('date')['amount'].sum().reset_index()
            fig_trend = px.bar(daily_spend, x='date', y='amount', title='Daily Spending Trend')
            col2.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No data for charts.")
