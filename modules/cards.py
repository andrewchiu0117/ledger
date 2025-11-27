import streamlit as st
import pandas as pd
import database as db
from modules import utils

def view():
    st.header("Credit Card Management")

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
        
        st.subheader("Card Usage Summary")
        if not card_usage.empty:
            st.bar_chart(card_usage.set_index('payment_method'))
            
            st.dataframe(card_usage.style.format({"amount": "{:.2f}"}), use_container_width=True)
        else:
            st.info("No credit card usage found.")
            
        # Detailed view per card
        st.subheader("Detailed Card Transactions")
        selected_card = st.selectbox("Select Card", card_methods)
        
        card_txs = expenses[expenses['payment_method'] == selected_card]
        if not card_txs.empty:
            st.dataframe(card_txs[['date', 'category', 'amount', 'description']].style.format({"amount": "{:.2f}"}), use_container_width=True)
            st.metric(label=f"Total {selected_card} Usage", value=utils.format_currency(card_txs['amount'].sum()))
        else:
            st.info(f"No transactions for {selected_card}")
            
    else:
        st.info("No transactions found.")
