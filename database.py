import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "money.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    description TEXT
                )''')
    
    # Budgets table
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                    month TEXT PRIMARY KEY,
                    amount REAL NOT NULL
                )''')
    
    # Stocks table
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    buy_date TEXT NOT NULL,
                    buy_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    broker_fee REAL DEFAULT 0,
                    transaction_fee REAL DEFAULT 0,
                    status TEXT DEFAULT 'Held'
                )''')
    
    # Accounts table
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    initial_balance REAL DEFAULT 0
                )''')

    # Categories table
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL
                )''')

    # Check if we need to migrate payment methods
    c.execute("SELECT count(*) FROM accounts")
    if c.fetchone()[0] == 0:
        from modules import utils
        for pm in utils.PAYMENT_METHODS:
             c.execute("INSERT INTO accounts (name, type, initial_balance) VALUES (?, ?, ?)", (pm, 'General', 0))
    
    # Check if we need to migrate categories
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        # Default categories - these will be migrated from utils.CATEGORIES
        default_categories = [
            ("Food", "Expense"),
            ("Transport", "Expense"),
            ("Entertainment", "Expense"),
            ("Shopping", "Expense"),
            ("Bills", "Expense"),
            ("Housing", "Expense"),
            ("Health", "Expense"),
            ("Education", "Expense"),
            ("Investment", "Both"),
            ("Salary", "Income"),
            ("Bonus", "Income"),
            ("Other", "Both")
        ]
        for name, cat_type in default_categories:
            c.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, cat_type))
    
    # Check if transactions table has account_id
    c.execute("PRAGMA table_info(transactions)")
    columns = [info[1] for info in c.fetchall()]
    if 'account_id' not in columns:
        c.execute("ALTER TABLE transactions ADD COLUMN account_id INTEGER")
        
        # Migrate existing data
        c.execute("SELECT id, name FROM accounts")
        accounts = {name: id for id, name in c.fetchall()}
        
        c.execute("SELECT id, payment_method FROM transactions")
        for tx_id, pm in c.fetchall():
            if pm in accounts:
                c.execute("UPDATE transactions SET account_id = ? WHERE id = ?", (accounts[pm], tx_id))

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

def add_transaction(date, type, category, amount, payment_method, description, account_id=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO transactions (date, type, category, amount, payment_method, description, account_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (date, type, category, amount, payment_method, description, account_id))
    conn.commit()
    conn.close()

def update_transaction(tx_id, date, type, category, amount, payment_method, description, account_id=None):
    """Update an existing transaction record.

    Parameters
    ----------
    tx_id: int
        The ID of the transaction to update.
    date: datetime.date or str
        New transaction date.
    type: str
        "Expense" or "Income".
    category: str
        Transaction category.
    amount: float
        Transaction amount.
    payment_method: str
        Account name or payment method.
    description: str
        Optional description.
    account_id: int, optional
        Foreign key to accounts table.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """UPDATE transactions SET date = ?, type = ?, category = ?, amount = ?, payment_method = ?, description = ?, account_id = ? WHERE id = ?""",
        (date, type, category, amount, payment_method, description, account_id, tx_id)
    )
    conn.commit()
    conn.close()

def delete_transaction(tx_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()

def get_transactions(limit=50):
    conn = get_connection()
    query = """
        SELECT t.*, a.name as account_name 
        FROM transactions t 
        LEFT JOIN accounts a ON t.account_id = a.id 
        ORDER BY t.date DESC LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df

def get_all_transactions():
    conn = get_connection()
    query = """
        SELECT t.*, a.name as account_name 
        FROM transactions t 
        LEFT JOIN accounts a ON t.account_id = a.id 
        ORDER BY t.date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def set_budget(month, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO budgets (month, amount) VALUES (?, ?)", (month, amount))
    conn.commit()
    conn.close()

def get_budget(month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT amount FROM budgets WHERE month = ?", (month,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def add_stock(symbol, buy_date, buy_price, quantity, broker_fee, transaction_fee):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO stocks (symbol, buy_date, buy_price, quantity, broker_fee, transaction_fee) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (symbol, buy_date, buy_price, quantity, broker_fee, transaction_fee))
    conn.commit()
    conn.close()

def get_stocks():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM stocks WHERE status = 'Held'", conn)
    conn.close()
    return df

# Initialize DB on import
init_db()

def add_account(name, type, initial_balance):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO accounts (name, type, initial_balance) VALUES (?, ?, ?)", (name, type, initial_balance))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_accounts():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM accounts", conn)
    conn.close()
    return df

def delete_account(account_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()

def get_account_balances():
    conn = get_connection()
    
    # Get accounts
    accounts_df = pd.read_sql_query("SELECT * FROM accounts", conn)
    
    # Get transactions grouped by account
    query = """
        SELECT account_id, type, SUM(amount) as total
        FROM transactions 
        WHERE account_id IS NOT NULL
        GROUP BY account_id, type
    """
    tx_df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    if accounts_df.empty:
        return pd.DataFrame(columns=['name', 'type', 'initial_balance', 'balance'])
        
    balances = []
    for _, account in accounts_df.iterrows():
        balance = account['initial_balance']
        
        if not tx_df.empty:
            # Add income
            income = tx_df[(tx_df['account_id'] == account['id']) & (tx_df['type'] == 'Income')]['total'].sum()
            # Subtract expenses
            expenses = tx_df[(tx_df['account_id'] == account['id']) & (tx_df['type'] == 'Expense')]['total'].sum()
            
            balance += (income - expenses)
            
        balances.append(balance)
        
    accounts_df['balance'] = balances
    return accounts_df

def add_category(name, type):
    """Add a new category to the database.
    
    Parameters
    ----------
    name: str
        Category name
    type: str
        Category type: 'Expense', 'Income', or 'Both'
    
    Returns
    -------
    bool
        True if successful, False if category already exists
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_categories(filter_type=None):
    """Get categories from the database.
    
    Parameters
    ----------
    filter_type: str, optional
        Filter by type: 'Expense', 'Income', or None for all
    
    Returns
    -------
    pandas.DataFrame
        DataFrame with category data
    """
    conn = get_connection()
    if filter_type:
        query = "SELECT * FROM categories WHERE type = ? OR type = 'Both' ORDER BY name"
        df = pd.read_sql_query(query, conn, params=(filter_type,))
    else:
        df = pd.read_sql_query("SELECT * FROM categories ORDER BY name", conn)
    conn.close()
    return df

def delete_category(category_id):
    """Delete a category from the database.
    
    Parameters
    ----------
    category_id: int
        ID of the category to delete
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()

