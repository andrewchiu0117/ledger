import streamlit as st
import database as db
import pandas as pd
from .utils import format_currency

def view():
    st.header("Account Management")

    # Add New Account
    with st.expander("Add New Account"):
        col1, col2 = st.columns(2)
        with col1:
            account_name = st.text_input("Account Name")
            account_type = st.selectbox("Type", ["Bank", "Credit Card", "Cash", "Investment", "Other"])
        
        with col2:
            initial_balance = st.number_input("Initial Balance", value=0.0)
        
        if st.button("Add Account"):
            if account_name:
                if db.add_account(account_name, account_type, initial_balance):
                    st.success(f"Account '{account_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Account name already exists.")
            else:
                st.error("Account name is required.")

    # View Accounts
    st.subheader("Your Accounts")
    
    # Calculate current balances
    accounts_df = db.get_accounts()
    transactions_df = db.get_all_transactions()
    
    if not accounts_df.empty:
        balances = []
        for _, account in accounts_df.iterrows():
            # Initial balance
            balance = account['initial_balance']
            
            # Add income, subtract expenses linked to this account
            if not transactions_df.empty:
                account_txs = transactions_df[transactions_df['account_id'] == account['id']]
                income = account_txs[account_txs['type'] == 'Income']['amount'].sum()
                expenses = account_txs[account_txs['type'] == 'Expense']['amount'].sum()
                balance += (income - expenses)
            
            balances.append(balance)
        
        accounts_df['Current Balance'] = balances
        
        # Display
        st.dataframe(
            accounts_df[['name', 'type', 'initial_balance', 'Current Balance']].style.format({
                "initial_balance": format_currency,
                "Current Balance": format_currency
            }),
            use_container_width=True
        )
        
        # Delete Account
        with st.expander("Delete Account"):
            account_to_delete = st.selectbox("Select Account to Delete", accounts_df['name'])
            if st.button("Delete Selected Account"):
                account_id = accounts_df[accounts_df['name'] == account_to_delete]['id'].values[0]
                db.delete_account(account_id)
                st.success(f"Account '{account_to_delete}' deleted.")
                st.rerun()
    else:
        st.info("No accounts found. Add one above.")
