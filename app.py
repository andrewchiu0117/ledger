import streamlit as st
from modules import dashboard, expenses, cards, stocks, accounts, categories, utils, monthly


st.set_page_config(page_title="個人理財追蹤器", layout="wide", page_icon="💰")

utils.load_css("modules/styles.css")

def main():
    st.sidebar.title("💰 理財追蹤器")
    
    page = st.sidebar.radio(
        "導航",
        ["儀表板", "支出", "每月統計", "帳戶", "類別", "信用卡", "股票"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.1.0")
    
    if page == "儀表板":
        dashboard.view()
    elif page == "支出":
        expenses.view()
    elif page == "每月統計":
        monthly.view()
    elif page == "帳戶":
        accounts.view()
    elif page == "類別":
        categories.view()
    elif page == "信用卡":
        cards.view()
    elif page == "股票":
        stocks.view()


if __name__ == "__main__":
    main()
