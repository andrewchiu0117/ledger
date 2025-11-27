import streamlit as st
from modules import dashboard, expenses, cards, stocks, accounts, categories, utils


st.set_page_config(page_title="Personal Finance Tracker", layout="wide", page_icon="💰")

utils.load_css("modules/styles.css")

def main():
    st.sidebar.title("💰 Money Tracker")
    
    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Expenses", "Accounts", "Categories", "Cards", "Stocks"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.1.0")
    
    if page == "Dashboard":
        dashboard.view()
    elif page == "Expenses":
        expenses.view()
    elif page == "Accounts":
        accounts.view()
    elif page == "Categories":
        categories.view()
    elif page == "Cards":
        cards.view()
    elif page == "Stocks":
        stocks.view()


if __name__ == "__main__":
    main()
