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
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

def add_transaction(date, type, category, amount, payment_method, description):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO transactions (date, type, category, amount, payment_method, description) VALUES (?, ?, ?, ?, ?, ?)",
              (date, type, category, amount, payment_method, description))
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
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC LIMIT ?", conn, params=(limit,))
    conn.close()
    return df

def get_all_transactions():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
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
