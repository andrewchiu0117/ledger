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
        
        # Fetch accounts
        accounts_df = db.get_accounts()
        account_names = accounts_df['name'].tolist() if not accounts_df.empty else []
        account_map = {row['name']: row['id'] for _, row in accounts_df.iterrows()}
        
        with col1:
            tx_date = st.date_input("Date", date.today())
            tx_type = st.selectbox("Type", ["Expense", "Income"])
            # Get categories based on transaction type
            categories = utils.get_categories(tx_type)
            category = st.selectbox("Category", categories)

        
        with col2:
            amount = st.number_input("Amount", min_value=0, step=1)
            # payment_method = st.selectbox("Payment Method", utils.PAYMENT_METHODS) # Deprecated
            account_name = st.selectbox("Account", account_names)
            description = st.text_input("Description")
        
        if st.button("Add Transaction"):
            if amount > 0:
                if account_name:
                    account_id = account_map[account_name]
                    # We still pass account_name as payment_method for backward compatibility or display in simple views if needed, 
                    # but ideally we rely on account_id. The DB function still takes payment_method.
                    db.add_transaction(tx_date, tx_type, category, amount, account_name, description, account_id)
                    st.success("Transaction added successfully!")
                    st.rerun()
                else:
                    st.error("Please select an account.")
            else:
                st.error("Amount must be greater than 0")

    # View Transactions
    st.subheader("Recent Transactions")
    df = db.get_transactions(limit=20)
    
    if not df.empty:
        # Display as a dataframe with some formatting
        # Show account_name instead of payment_method if available
        display_cols = ['date', 'type', 'category', 'amount', 'account_name', 'description']
        # If account_name is null (legacy), fallback to payment_method might be needed, but our query handles it via join.
        # However, if join fails (account deleted), it might be null.
        # Let's just show what we have.
        
        st.dataframe(df[display_cols].style.format({"amount": utils.format_currency}), use_container_width=True)
        
        # Delete Transaction
        # Delete Transaction
        with st.expander("Delete Transaction"):
            tx_id_to_delete = st.number_input("Enter Transaction ID to delete", min_value=0, step=1, key="delete_tx_id")
            if st.button("Delete", key="delete_btn"):
                db.delete_transaction(tx_id_to_delete)
                st.success(f"Transaction {tx_id_to_delete} deleted.")
                st.rerun()

        # Edit Transaction
        with st.expander("Edit Transaction"):
            edit_tx_id = st.number_input("Enter Transaction ID to edit", min_value=0, step=1, key="edit_tx_id")
            # Load existing transaction details
            if st.button("Load", key="load_btn"):
                tx_df = db.get_transactions(limit=1000)  # fetch all
                tx_row = tx_df[tx_df['id'] == edit_tx_id]
                if not tx_row.empty:
                    tx = tx_row.iloc[0]
                    st.session_state['edit_date'] = pd.to_datetime(tx['date']).date()
                    st.session_state['edit_type'] = tx['type']
                    st.session_state['edit_category'] = tx['category']
                    st.session_state['edit_amount'] = tx['amount']
                    st.session_state['edit_account'] = tx.get('account_name', '')
                    st.session_state['edit_description'] = tx['description']
                else:
                    st.error("Transaction ID not found.")
            if 'edit_date' in st.session_state:
                col1, col2 = st.columns(2)
                with col1:
                    edit_date = st.date_input("Date", st.session_state['edit_date'], key="edit_date_input")
                    edit_type = st.selectbox("Type", ["Expense", "Income"], index=0 if st.session_state['edit_type'] == "Expense" else 1, key="edit_type_input")
                    # Get categories based on transaction type
                    edit_categories = utils.get_categories(edit_type)
                    current_category = st.session_state['edit_category']
                    category_index = edit_categories.index(current_category) if current_category in edit_categories else 0
                    edit_category = st.selectbox("Category", edit_categories, index=category_index, key="edit_category_input")

                with col2:
                    edit_amount = st.number_input("Amount", min_value=0.0, step=1.0, value=st.session_state['edit_amount'], key="edit_amount_input")
                    # Account selection
                    accounts_df = db.get_accounts()
                    account_names = accounts_df['name'].tolist()
                    account_map = {row['name']: row['id'] for _, row in accounts_df.iterrows()}
                    edit_account_name = st.selectbox("Account", account_names, index=account_names.index(st.session_state['edit_account']) if st.session_state['edit_account'] in account_names else 0, key="edit_account_input")
                    edit_description = st.text_input("Description", st.session_state['edit_description'], key="edit_description_input")
                if st.button("Update Transaction", key="update_btn"):
                    account_id = account_map.get(edit_account_name)
                    db.update_transaction(edit_tx_id, edit_date, edit_type, edit_category, edit_amount, edit_account_name, edit_description, account_id)
                    st.success(f"Transaction {edit_tx_id} updated.")
                    # Clear session state
                    for k in ['edit_date','edit_type','edit_category','edit_amount','edit_account','edit_description']:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
    else:
        st.info("No transactions found.")
