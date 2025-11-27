CATEGORIES = [
    "Food", "Transport", "Entertainment", "Shopping", "Bills", "Housing", "Health", "Education", "Investment", "Salary", "Bonus", "Other"
]

PAYMENT_METHODS = [
    "Cash", "Credit Card", "Go Card", "Cube Card", "iLeo Card", "Line Bank", "Richart", "Debit Card", "Bank Transfer"
]

def format_currency(amount):
    return f"${amount:,.2f}"
