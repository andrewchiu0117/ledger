import streamlit as st
import pandas as pd
from datetime import date
import database as db
from modules import utils

def view():
    st.header("交易管理")

    # Add New Transaction
    with st.expander("新增交易", expanded=True):
        col1, col2 = st.columns(2)
        
        # Fetch accounts
        accounts_df = db.get_accounts()
        account_names = accounts_df['name'].tolist() if not accounts_df.empty else []
        account_map = {row['name']: row['id'] for _, row in accounts_df.iterrows()}
        
        with col1:
            tx_date = st.date_input("日期", date.today())
            tx_type = st.selectbox("類型", ["支出", "收入"])
            # Get categories based on transaction type
            tx_type_db = "Expense" if tx_type == "支出" else "Income"
            categories = utils.get_categories(tx_type_db)
            category = st.selectbox("類別", categories)

        
        with col2:
            amount = st.number_input("金額", min_value=0, step=1)
            # payment_method = st.selectbox("Payment Method", utils.PAYMENT_METHODS) # Deprecated
            account_name = st.selectbox("帳戶", account_names)
            description = st.text_input("備註")
        
        if st.button("新增交易"):
            if amount > 0:
                if account_name:
                    account_id = account_map[account_name]
                    # We still pass account_name as payment_method for backward compatibility or display in simple views if needed, 
                    # but ideally we rely on account_id. The DB function still takes payment_method.
                    db.add_transaction(tx_date, tx_type_db, category, amount, account_name, description, account_id)
                    st.success("交易新增成功！")
                    st.rerun()
                else:
                    st.error("請選擇帳戶。")
            else:
                st.error("金額必須大於 0")

    # View Transactions
    st.subheader("最近交易")
    df = db.get_transactions(limit=20)
    
    if not df.empty:
        # Display as a dataframe with some formatting
        # Show account_name instead of payment_method if available
        display_cols = ['date', 'type', 'category', 'amount', 'account_name', 'description']
        # If account_name is null (legacy), fallback to payment_method might be needed, but our query handles it via join.
        # However, if join fails (account deleted), it might be null.
        # Let's just show what we have.
        
        # Translate type column for display
        df_display = df[display_cols].copy()
        df_display['type'] = df_display['type'].map({'Income': '收入', 'Expense': '支出'})
        df_display.columns = ['日期', '類型', '類別', '金額', '帳戶', '備註']
        
        # Format currency column
        df_display['金額'] = df_display['金額'].apply(lambda x: utils.format_currency(x) if isinstance(x, (int, float)) else x)
        st.dataframe(df_display, use_container_width=True)
        
        # Delete Transaction
        # Delete Transaction
        with st.expander("刪除交易"):
            tx_id_to_delete = st.number_input("輸入要刪除的交易 ID", min_value=0, step=1, key="delete_tx_id")
            if st.button("刪除", key="delete_btn"):
                db.delete_transaction(tx_id_to_delete)
                st.success(f"交易 {tx_id_to_delete} 已刪除。")
                st.rerun()

        # Edit Transaction
        with st.expander("編輯交易"):
            edit_tx_id = st.number_input("輸入要編輯的交易 ID", min_value=0, step=1, key="edit_tx_id")
            # Load existing transaction details
            if st.button("載入", key="load_btn"):
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
                    st.error("找不到該交易 ID。")
            if 'edit_date' in st.session_state:
                col1, col2 = st.columns(2)
                with col1:
                    edit_date = st.date_input("日期", st.session_state['edit_date'], key="edit_date_input")
                    edit_type_display = "支出" if st.session_state['edit_type'] == "Expense" else "收入"
                    edit_type = st.selectbox("類型", ["支出", "收入"], index=0 if st.session_state['edit_type'] == "Expense" else 1, key="edit_type_input")
                    edit_type_db = "Expense" if edit_type == "支出" else "Income"
                    # Get categories based on transaction type
                    edit_categories = utils.get_categories(edit_type_db)
                    current_category = st.session_state['edit_category']
                    category_index = edit_categories.index(current_category) if current_category in edit_categories else 0
                    edit_category = st.selectbox("類別", edit_categories, index=category_index, key="edit_category_input")

                with col2:
                    edit_amount = st.number_input("金額", min_value=0.0, step=1.0, value=st.session_state['edit_amount'], key="edit_amount_input")
                    # Account selection
                    accounts_df = db.get_accounts()
                    account_names = accounts_df['name'].tolist()
                    account_map = {row['name']: row['id'] for _, row in accounts_df.iterrows()}
                    edit_account_name = st.selectbox("帳戶", account_names, index=account_names.index(st.session_state['edit_account']) if st.session_state['edit_account'] in account_names else 0, key="edit_account_input")
                    edit_description = st.text_input("備註", st.session_state['edit_description'], key="edit_description_input")
                if st.button("更新交易", key="update_btn"):
                    account_id = account_map.get(edit_account_name)
                    db.update_transaction(edit_tx_id, edit_date, edit_type_db, edit_category, edit_amount, edit_account_name, edit_description, account_id)
                    st.success(f"交易 {edit_tx_id} 已更新。")
                    # Clear session state
                    for k in ['edit_date','edit_type','edit_category','edit_amount','edit_account','edit_description']:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
    else:
        st.info("找不到交易記錄。")
