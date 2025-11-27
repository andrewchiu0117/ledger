import streamlit as st
import pandas as pd
from datetime import date
import database as db
from modules import utils

def view():
    st.header("Expense Management")

    # Add New Transaction
    with st.expander("Add New Transaction", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tx_date = st.date_input("Date", date.today())
            tx_type = st.selectbox("Type", ["Expense", "Income"])
            category = st.selectbox("Category", utils.CATEGORIES)
        
        with col2:
            amount = st.number_input("Amount", min_value=0.0, step=1.0)
            payment_method = st.selectbox("Payment Method", utils.PAYMENT_METHODS)
            description = st.text_input("Description")
        
        if st.button("Add Transaction"):
            if amount > 0:
                db.add_transaction(tx_date, tx_type, category, amount, payment_method, description)
                st.success("Transaction added successfully!")
                st.rerun()
            else:
                st.error("Amount must be greater than 0")

    # View Transactions
    st.subheader("Recent Transactions")
    df = db.get_transactions(limit=20)
    
    if not df.empty:
        # Display as a dataframe with some formatting
        st.dataframe(df.style.format({"amount": "{:.2f}"}), use_container_width=True)
        
        # Delete Transaction
        with st.expander("Delete Transaction"):
            tx_id_to_delete = st.number_input("Enter Transaction ID to delete", min_value=0, step=1)
            if st.button("Delete"):
                db.delete_transaction(tx_id_to_delete)
                st.success(f"Transaction {tx_id_to_delete} deleted.")
                st.rerun()
    else:
        st.info("No transactions found.")
