import streamlit as st
from modules import dashboard, expenses, cards, stocks

st.set_page_config(page_title="Personal Finance Tracker", layout="wide", page_icon="💰")

def main():
    st.sidebar.title("💰 Money Tracker")
    
    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Expenses", "Cards", "Stocks"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0.0")
    
    if page == "Dashboard":
        dashboard.view()
    elif page == "Expenses":
        expenses.view()
    elif page == "Cards":
        cards.view()
    elif page == "Stocks":
        stocks.view()

if __name__ == "__main__":
    main()
