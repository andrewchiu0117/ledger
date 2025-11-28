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
    st.header("股票投資組合")

    # Add New Stock Purchase
    with st.expander("記錄股票購買", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("股票代號（例如：AAPL, 2330.TW）").upper()
            buy_date = st.date_input("購買日期")
            quantity = st.number_input("數量", min_value=0.0, step=1.0)
        
        with col2:
            buy_price = st.number_input("買入價格（每股）", min_value=0.0, step=0.01)
            broker_fee = st.number_input("券商手續費", min_value=0.0, step=1.0)
            transaction_fee = st.number_input("交易稅", min_value=0.0, step=1.0)
        
        if st.button("記錄購買"):
            if symbol and quantity > 0 and buy_price > 0:
                db.add_stock(symbol, buy_date, buy_price, quantity, broker_fee, transaction_fee)
                st.success(f"已記錄 {symbol} 的購買")
                st.rerun()
            else:
                st.error("請填寫所有必填欄位。")

    # Portfolio View
    st.subheader("目前持股")
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
            with st.spinner('正在取得目前股價...'):
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
        display_df = df[display_cols].copy()
        display_df.columns = ['股票代號', '數量', '平均成本', '目前價格', '市值', '損益', '報酬率']
        
        # Format columns
        display_df['數量'] = display_df['數量'].apply(lambda x: f"{x:.2f}")
        display_df['平均成本'] = display_df['平均成本'].apply(lambda x: utils.format_currency(x) if pd.notna(x) and isinstance(x, (int, float)) else "N/A")
        display_df['目前價格'] = display_df['目前價格'].apply(lambda x: utils.format_currency(x) if pd.notna(x) and isinstance(x, (int, float)) else "N/A")
        display_df['市值'] = display_df['市值'].apply(lambda x: utils.format_currency(x) if pd.notna(x) and isinstance(x, (int, float)) else "N/A")
        display_df['損益'] = display_df['損益'].apply(lambda x: utils.format_currency(x) if pd.notna(x) and isinstance(x, (int, float)) else "N/A")
        display_df['報酬率'] = display_df['報酬率'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and isinstance(x, (int, float)) else "N/A")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Total Summary
        total_invested = df['total_cost'].sum()
        total_value = df['market_value'].sum()
        total_pl = total_value - total_invested
        
        col1, col2, col3 = st.columns(3)
        col1.metric("總投資金額", utils.format_currency(total_invested))
        col2.metric("目前市值", utils.format_currency(total_value), delta=utils.format_currency(total_pl))
        col3.metric("總報酬率", f"{(total_pl/total_invested)*100:.2f}%" if total_invested > 0 else "0%")
        
    else:
        st.info("投資組合中沒有股票。")
