import streamlit as st
import pandas as pd
import database as db
from modules import utils

def view():
    st.header("信用卡管理")

    # Filter transactions for credit cards
    # We assume anything not "Cash" or "Bank Transfer" might be a card, or we just look for specific ones.
    # For this simple app, we'll just show stats for all payment methods that are likely cards.
    
    card_methods = [m for m in utils.PAYMENT_METHODS if "Card" in m or m in ["Line Bank", "Richart"]]
    
    df = db.get_all_transactions()
    
    if not df.empty:
        # Filter for expenses only
        expenses = df[df['type'] == 'Expense']
        
        # Group by payment method
        card_usage = expenses[expenses['payment_method'].isin(card_methods)].groupby('payment_method')['amount'].sum().reset_index()
        
        st.subheader("信用卡使用摘要")
        if not card_usage.empty:
            st.bar_chart(card_usage.set_index('payment_method'))
            
            display_df = card_usage.copy()
            display_df.columns = ['支付方式', '金額']
            display_df['金額'] = display_df['金額'].apply(utils.format_currency)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("找不到信用卡使用記錄。")
            
        # Detailed view per card
        st.subheader("詳細信用卡交易")
        selected_card = st.selectbox("選擇信用卡", card_methods)
        
        card_txs = expenses[expenses['payment_method'] == selected_card]
        if not card_txs.empty:
            display_txs = card_txs[['date', 'category', 'amount', 'description']].copy()
            display_txs.columns = ['日期', '類別', '金額', '備註']
            display_txs['金額'] = display_txs['金額'].apply(utils.format_currency)
            st.dataframe(display_txs, use_container_width=True)
            st.metric(label=f"{selected_card} 總使用金額", value=utils.format_currency(card_txs['amount'].sum()))
        else:
            st.info(f"{selected_card} 沒有交易記錄")
            
    else:
        st.info("找不到交易記錄。")
