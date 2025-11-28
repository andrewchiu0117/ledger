import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import database as db
from modules import utils

def view():
    st.header("每月收支統計")
    
    # Fetch all transactions
    df_tx = db.get_all_transactions()
    
    if df_tx.empty:
        st.info("尚無交易資料。")
        return
    
    # Convert date to datetime
    df_tx['date'] = pd.to_datetime(df_tx['date'])
    
    # Group by month
    df_tx['year_month'] = df_tx['date'].dt.to_period('M').astype(str)
    
    # Calculate monthly income and expenses
    monthly_data = []
    for month in sorted(df_tx['year_month'].unique(), reverse=True):
        month_df = df_tx[df_tx['year_month'] == month]
        
        income = month_df[month_df['type'] == 'Income']['amount'].sum()
        expenses = month_df[month_df['type'] == 'Expense']['amount'].sum()
        net = income - expenses
        
        monthly_data.append({
            '月份': month,
            '收入': income,
            '支出': expenses,
            '淨額': net
        })
    
    monthly_df = pd.DataFrame(monthly_data)
    
    # Display summary metrics
    if not monthly_df.empty:
        latest_month = monthly_df.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新月份", latest_month['月份'])
        col2.metric("收入", utils.format_currency(latest_month['收入']))
        col3.metric("支出", utils.format_currency(latest_month['支出']))
        col4.metric("淨額", utils.format_currency(latest_month['淨額']), 
                   delta=utils.format_currency(latest_month['淨額']))
    
    st.subheader("每月收支明細")
    
    # Format the dataframe for display
    display_df = monthly_df.copy()
    display_df['收入'] = display_df['收入'].apply(lambda x: utils.format_currency(x))
    display_df['支出'] = display_df['支出'].apply(lambda x: utils.format_currency(x))
    display_df['淨額'] = display_df['淨額'].apply(lambda x: utils.format_currency(x))
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Charts
    st.subheader("趨勢分析")
    col1, col2 = st.columns(2)
    
    # Monthly income and expenses line chart
    fig_trend = px.line(
        monthly_df, 
        x='月份', 
        y=['收入', '支出', '淨額'],
        title='每月收支趨勢',
        labels={'value': '金額', 'variable': '類型'},
        markers=True
    )
    fig_trend.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    col1.plotly_chart(fig_trend, use_container_width=True)
    
    # Monthly comparison bar chart
    fig_bar = px.bar(
        monthly_df,
        x='月份',
        y=['收入', '支出'],
        title='每月收入與支出比較',
        labels={'value': '金額', 'variable': '類型'},
        barmode='group'
    )
    fig_bar.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    col2.plotly_chart(fig_bar, use_container_width=True)
    
    # Monthly net amount bar chart
    st.subheader("每月淨額")
    fig_net = px.bar(
        monthly_df,
        x='月份',
        y='淨額',
        title='每月淨額（收入 - 支出）',
        labels={'淨額': '淨額', '月份': '月份'},
        color='淨額',
        color_continuous_scale=['red', 'yellow', 'green']
    )
    fig_net.update_layout(showlegend=False)
    st.plotly_chart(fig_net, use_container_width=True)
    
    # Detailed view for selected month
    st.subheader("月份詳細資料")
    if not monthly_df.empty:
        selected_month = st.selectbox("選擇月份", monthly_df['月份'].tolist())
        
        if selected_month:
            month_tx = df_tx[df_tx['year_month'] == selected_month].copy()
            
            # Income breakdown
            st.write(f"**{selected_month} 收入明細**")
            income_df = month_tx[month_tx['type'] == 'Income'][['date', 'category', 'amount', 'account_name', 'description']].copy()
            income_df['date'] = income_df['date'].dt.strftime('%Y-%m-%d')
            income_df = income_df.sort_values('date', ascending=False)
            if not income_df.empty:
                income_df['amount'] = income_df['amount'].apply(lambda x: utils.format_currency(x))
                st.dataframe(income_df, use_container_width=True, hide_index=True)
                
                # Income by category
                income_by_cat = month_tx[month_tx['type'] == 'Income'].groupby('category')['amount'].sum().reset_index()
                income_by_cat.columns = ['類別', '金額']
                income_by_cat['金額'] = income_by_cat['金額'].apply(lambda x: utils.format_currency(x))
                st.dataframe(income_by_cat, use_container_width=True, hide_index=True)
            else:
                st.info("該月份無收入記錄。")
            
            # Expense breakdown
            st.write(f"**{selected_month} 支出明細**")
            expense_df = month_tx[month_tx['type'] == 'Expense'][['date', 'category', 'amount', 'account_name', 'description']].copy()
            expense_df['date'] = expense_df['date'].dt.strftime('%Y-%m-%d')
            expense_df = expense_df.sort_values('date', ascending=False)
            if not expense_df.empty:
                expense_df['amount'] = expense_df['amount'].apply(lambda x: utils.format_currency(x))
                st.dataframe(expense_df, use_container_width=True, hide_index=True)
                
                # Expenses by category
                expense_by_cat = month_tx[month_tx['type'] == 'Expense'].groupby('category')['amount'].sum().reset_index()
                expense_by_cat.columns = ['類別', '金額']
                expense_by_cat = expense_by_cat.sort_values('金額', ascending=False)
                expense_by_cat['金額'] = expense_by_cat['金額'].apply(lambda x: utils.format_currency(x))
                st.dataframe(expense_by_cat, use_container_width=True, hide_index=True)
            else:
                st.info("該月份無支出記錄。")



