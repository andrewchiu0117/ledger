import streamlit as st
import database as db
import pandas as pd
from .utils import format_currency

def view():
    st.header("帳戶管理")

    # Add New Account
    with st.expander("新增帳戶"):
        col1, col2 = st.columns(2)
        with col1:
            account_name = st.text_input("帳戶名稱")
            account_type = st.selectbox("類型", ["銀行", "信用卡", "現金", "投資", "其他"])
        
        with col2:
            initial_balance = st.number_input("初始餘額", value=0.0)
        
        if st.button("新增帳戶"):
            if account_name:
                account_type_db = {"銀行": "Bank", "信用卡": "Credit Card", "現金": "Cash", "投資": "Investment", "其他": "Other"}[account_type]
                if db.add_account(account_name, account_type_db, initial_balance):
                    st.success(f"帳戶 '{account_name}' 新增成功！")
                    st.rerun()
                else:
                    st.error("帳戶名稱已存在。")
            else:
                st.error("請輸入帳戶名稱。")

    # View Accounts
    st.subheader("您的帳戶")
    
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
        
        # Translate account types for display
        type_map = {"Bank": "銀行", "Credit Card": "信用卡", "Cash": "現金", "Investment": "投資", "Other": "其他"}
        accounts_df['type'] = accounts_df['type'].map(type_map)
        
        # Display
        display_df = accounts_df[['name', 'type', 'initial_balance', 'Current Balance']].copy()
        display_df.columns = ['帳戶名稱', '類型', '初始餘額', '目前餘額']
        
        # Format currency columns
        display_df['初始餘額'] = display_df['初始餘額'].apply(format_currency)
        display_df['目前餘額'] = display_df['目前餘額'].apply(format_currency)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Delete Account
        with st.expander("刪除帳戶"):
            account_to_delete = st.selectbox("選擇要刪除的帳戶", accounts_df['name'])
            if st.button("刪除選取的帳戶"):
                account_id = accounts_df[accounts_df['name'] == account_to_delete]['id'].values[0]
                db.delete_account(account_id)
                st.success(f"帳戶 '{account_to_delete}' 已刪除。")
                st.rerun()
    else:
        st.info("找不到帳戶。請在上方新增一個。")
