import streamlit as st
import pandas as pd
import yfinance as yf
import database as db
from modules import utils

def get_current_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        if not history.empty:
            return history['Close'].iloc[-1]
    except Exception:
        pass
    return None

def view():
    st.header("Stock Portfolio")

    # Add New Stock Purchase
    with st.expander("Record Stock Purchase", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Stock Symbol (e.g., AAPL, 2330.TW)").upper()
            buy_date = st.date_input("Buy Date")
            quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
        
        with col2:
            buy_price = st.number_input("Buy Price (per share)", min_value=0.0, step=0.01)
            broker_fee = st.number_input("Broker Fee", min_value=0.0, step=1.0)
            transaction_fee = st.number_input("Transaction Fee", min_value=0.0, step=1.0)
        
        if st.button("Record Purchase"):
            if symbol and quantity > 0 and buy_price > 0:
                db.add_stock(symbol, buy_date, buy_price, quantity, broker_fee, transaction_fee)
                st.success(f"Recorded purchase of {symbol}")
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

    # Portfolio View
    st.subheader("Current Holdings")
    df = db.get_stocks()
    
    if not df.empty:
        # Calculate costs
        df['total_cost'] = (df['buy_price'] * df['quantity']) + df['broker_fee'] + df['transaction_fee']
        df['avg_cost'] = df['total_cost'] / df['quantity']
        
        # Fetch current prices
        unique_symbols = df['symbol'].unique()
        current_prices = {}
        
        # Show a progress bar for fetching prices if there are many
        if len(unique_symbols) > 0:
            with st.spinner('Fetching current stock prices...'):
                for sym in unique_symbols:
                    price = get_current_price(sym)
                    if price:
                        current_prices[sym] = price
        
        df['current_price'] = df['symbol'].map(current_prices)
        df['market_value'] = df['current_price'] * df['quantity']
        df['profit_loss'] = df['market_value'] - df['total_cost']
        df['roi'] = (df['profit_loss'] / df['total_cost']) * 100
        
        # Display
        display_cols = ['symbol', 'quantity', 'avg_cost', 'current_price', 'market_value', 'profit_loss', 'roi']
        st.dataframe(df[display_cols].style.format({
            "quantity": "{:.2f}",
            "avg_cost": "{:.2f}",
            "current_price": "{:.2f}",
            "market_value": "{:.2f}",
            "profit_loss": "{:.2f}",
            "roi": "{:.2f}%"
        }), use_container_width=True)
        
        # Total Summary
        total_invested = df['total_cost'].sum()
        total_value = df['market_value'].sum()
        total_pl = total_value - total_invested
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invested", utils.format_currency(total_invested))
        col2.metric("Current Value", utils.format_currency(total_value), delta=utils.format_currency(total_pl))
        col3.metric("Total ROI", f"{(total_pl/total_invested)*100:.2f}%" if total_invested > 0 else "0%")
        
    else:
        st.info("No stocks found in portfolio.")
