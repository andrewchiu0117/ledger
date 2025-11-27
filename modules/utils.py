import streamlit as st

# Legacy hardcoded categories - kept for reference but not used
# CATEGORIES = [
#     "Food", "Transport", "Entertainment", "Shopping", "Bills", "Housing", "Health", "Education", "Investment", "Salary", "Bonus", "Other"
# ]

def get_categories(filter_type=None):
    """Get categories from database.
    
    Parameters
    ----------
    filter_type: str, optional
        Filter by type: 'Expense', 'Income', or None for all
    
    Returns
    -------
    list
        List of category names
    """
    import database as db
    df = db.get_categories(filter_type)
    return df['name'].tolist() if not df.empty else []


PAYMENT_METHODS = [
    "Cash", "Credit Card", "Go Card", "Cube Card", "iLeo Card", "Line Bank", "Richart", "Debit Card", "Bank Transfer"
]

def format_currency(amount):
    if amount == int(amount):
        return f"NT${int(amount):,}"
    return f"NT${amount:,.2f}"

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

