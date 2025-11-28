import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import database as db
from modules import utils, stocks

def categorize_account(account_name, account_type):
    """Categorize account into 活存, 定存, or 美金"""
    account_name_lower = account_name.lower()
    
    # Check for USD accounts
    if any(keyword in account_name_lower for keyword in ['usd', '美金', '美元', 'dollar']):
        return '美金'
    
    # Check for fixed deposits
    if '定存' in account_name or account_type == 'Fixed Deposit':
        return '定存'
    
    # Default to current deposit (活存)
    if account_type == 'Bank':
        return '活存'
    
    return '活存'

def categorize_stock(symbol):
    """Categorize stock as 台股 or 美股"""
    if symbol.endswith('.TW'):
        return '台股'
    return '美股'

def calculate_monthly_assets(df_tx, accounts_df, df_stocks, end_date=None):
    """Calculate total assets for each month up to end_date"""
    if end_date is None:
        end_date = date.today()
    
    monthly_assets = []
    
    # Work with a copy to avoid modifying original
    if not df_tx.empty:
        df_tx_copy = df_tx.copy()
    else:
        df_tx_copy = pd.DataFrame()
    
    # Get all unique months from transactions
    if not df_tx_copy.empty:
        # Ensure date is datetime
        if not pd.api.types.is_datetime64_any_dtype(df_tx_copy['date']):
            df_tx_copy['date'] = pd.to_datetime(df_tx_copy['date'])
        months = df_tx_copy['date'].dt.to_period('M').unique()
    else:
        months = []
    
    # Add current month if not in list
    current_month = pd.Period(end_date.strftime("%Y-%m"), freq='M')
    if current_month not in months:
        months = list(months) + [current_month]
    
    months = sorted(months)
    
    for month in months:
        month_str = str(month)
        month_end = month.to_timestamp() + pd.offsets.MonthEnd(0)
        
        # Calculate account balances up to this month
        month_liquid = 0
        if not accounts_df.empty:
            for _, account in accounts_df.iterrows():
                balance = account['initial_balance']
                
                if not df_tx_copy.empty:
                    # Filter transactions up to this month
                    month_tx = df_tx_copy[df_tx_copy['date'] <= month_end]
                    account_txs = month_tx[month_tx['account_id'] == account['id']]
                    income = account_txs[account_txs['type'] == 'Income']['amount'].sum()
                    expenses = account_txs[account_txs['type'] == 'Expense']['amount'].sum()
                    balance += (income - expenses)
                
                month_liquid += balance
        
        # Calculate stock value (using buy price * quantity for simplicity)
        month_stock = 0
        if not df_stocks.empty:
            df_stocks_copy = df_stocks.copy()
            df_stocks_copy['buy_date'] = pd.to_datetime(df_stocks_copy['buy_date'])
            month_stock_df = df_stocks_copy[df_stocks_copy['buy_date'] <= month_end]
            month_stock = (month_stock_df['buy_price'] * month_stock_df['quantity']).sum()
        
        monthly_assets.append({
            'month': month_str,
            'total_assets': month_liquid + month_stock
        })
    
    return pd.DataFrame(monthly_assets)

def view():
    st.header("儀表板")
    
    # Date Filter (Default to current month)
    today = date.today()
    current_month_str = today.strftime("%Y-%m")
    
    # Fetch Data
    df_tx = db.get_all_transactions()
    df_stocks = db.get_stocks()
    
    # Calculate Totals
    total_income = 0
    total_expenses = 0
    monthly_expenses = 0
    
    if not df_tx.empty:
        # Convert date to datetime
        df_tx['date'] = pd.to_datetime(df_tx['date'])
        
        total_income = df_tx[df_tx['type'] == 'Income']['amount'].sum()
        total_expenses = df_tx[df_tx['type'] == 'Expense']['amount'].sum()
        
        # Monthly Expenses
        mask = (df_tx['date'].dt.to_period('M') == current_month_str) & (df_tx['type'] == 'Expense')
        monthly_expenses = df_tx[mask]['amount'].sum()

    # Stock Value
    stock_value = 0
    if not df_stocks.empty:
        stock_value = (df_stocks['buy_price'] * df_stocks['quantity']).sum() 
    
    # Account Balances (Liquid Assets)
    accounts_df = db.get_account_balances()
    liquid_assets = accounts_df['balance'].sum() if not accounts_df.empty else 0
    
    # Budget
    budget = db.get_budget(current_month_str)
    if budget == 0:
        budget = 30000 # Default default
    
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總資產", utils.format_currency(liquid_assets + stock_value))
    col2.metric("本月支出", utils.format_currency(monthly_expenses), delta=utils.format_currency(budget - monthly_expenses))
    col3.metric("本月預算", utils.format_currency(budget))
    col4.metric("股票成本", utils.format_currency(stock_value))
    
    # Budget Progress
    st.subheader("本月預算進度")
    progress = min(monthly_expenses / budget, 1.0) if budget > 0 else 0
    st.progress(progress)
    st.caption(f"已花費 {utils.format_currency(monthly_expenses)} / {utils.format_currency(budget)}")
    
    # Set Budget
    with st.expander("調整預算"):
        new_budget = st.number_input("設定本月預算", value=float(budget))
        if st.button("更新預算"):
            db.set_budget(current_month_str, new_budget)
            st.rerun()

    # Asset Analysis Section
    st.subheader("資產分析")
    
    # 1. Total Asset Proportion Pie Chart
    if not accounts_df.empty or not df_stocks.empty:
        asset_data = {
            '活存': 0,
            '定存': 0,
            '美金': 0,
            '台股': 0,
            '美股': 0
        }
        
        # Categorize accounts
        if not accounts_df.empty:
            for _, account in accounts_df.iterrows():
                category = categorize_account(account['name'], account['type'])
                asset_data[category] += account['balance']
        
        # Categorize stocks
        if not df_stocks.empty:
            for _, stock in df_stocks.iterrows():
                category = categorize_stock(stock['symbol'])
                stock_value_item = stock['buy_price'] * stock['quantity']
                asset_data[category] += stock_value_item
        
        # Filter out zero values
        asset_data_filtered = {k: v for k, v in asset_data.items() if v > 0}
        
        if asset_data_filtered:
            col1, col2 = st.columns(2)
            
            # Total Asset Proportion Pie Chart
            asset_df = pd.DataFrame(list(asset_data_filtered.items()), columns=['類別', '金額'])
            fig_asset = px.pie(asset_df, values='金額', names='類別', title='總資產比例分布')
            col1.plotly_chart(fig_asset, use_container_width=True)
            
            # Current Deposit Allocation (活存 accounts only)
            if not accounts_df.empty:
                current_deposit_accounts = []
                for _, account in accounts_df.iterrows():
                    category = categorize_account(account['name'], account['type'])
                    if category == '活存' and account['balance'] > 0:
                        current_deposit_accounts.append({
                            '帳戶': account['name'],
                            '餘額': account['balance']
                        })
                
                if current_deposit_accounts:
                    deposit_df = pd.DataFrame(current_deposit_accounts)
                    fig_deposit = px.pie(deposit_df, values='餘額', names='帳戶', title='活存配置圖')
                    col2.plotly_chart(fig_deposit, use_container_width=True)
                else:
                    col2.info("目前沒有活存帳戶資料")
            else:
                col2.info("目前沒有帳戶資料")
        else:
            st.info("目前沒有資產資料可供顯示")
    
    # 2. Monthly Asset Trend Chart
    st.subheader("資產趨勢")
    if not df_tx.empty or not accounts_df.empty or not df_stocks.empty:
        monthly_assets_df = calculate_monthly_assets(df_tx, accounts_df, df_stocks, today)
        if not monthly_assets_df.empty:
            fig_trend = px.line(monthly_assets_df, x='month', y='total_assets', 
                               title='每月資產趨勢圖', markers=True)
            fig_trend.update_layout(xaxis_title='月份', yaxis_title='總資產 (NT$)')
            fig_trend.update_traces(line=dict(width=3))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("目前沒有足夠的歷史資料來顯示資產趨勢")
    else:
        st.info("目前沒有資料可供顯示資產趨勢")

    # 3. This Month's Spending Items Pie Chart
    st.subheader("本月支出分析")
    if not df_tx.empty:
        # Filter to current month expenses
        current_month_expenses = df_tx[
            (df_tx['date'].dt.to_period('M') == current_month_str) & 
            (df_tx['type'] == 'Expense')
        ]
        
        if not current_month_expenses.empty:
            expense_by_category = current_month_expenses.groupby('category')['amount'].sum().reset_index()
            expense_by_category.columns = ['類別', '金額']
            
            fig_monthly_expense = px.pie(expense_by_category, values='金額', names='類別', 
                                        title='本月花費項目分布')
            st.plotly_chart(fig_monthly_expense, use_container_width=True)
        else:
            st.info("本月尚無支出記錄")
    else:
        st.info("尚無交易資料")

    # Original Charts Section
    st.subheader("支出分析")
    col1, col2 = st.columns(2)
    
    if not df_tx.empty:
        # Expense by Category (All time)
        expenses_df = df_tx[df_tx['type'] == 'Expense']
        if not expenses_df.empty:
            fig_cat = px.pie(expenses_df, values='amount', names='category', title='支出類別分布（全部）')
            col1.plotly_chart(fig_cat, use_container_width=True)
            
            # Daily Spending Trend
            daily_spend = expenses_df.groupby('date')['amount'].sum().reset_index()
            fig_trend = px.bar(daily_spend, x='date', y='amount', title='每日支出趨勢')
            col2.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("尚無資料可供圖表顯示。")
