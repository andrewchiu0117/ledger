"""
Google Sheets integration module for reading data from Google Sheets.
"""
import pandas as pd
import os
from typing import Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("Warning: gspread not available. Install with: pip install gspread google-auth")

# Google Sheets configuration
SPREADSHEET_ID = "1i1hT5FTRsNTBBVvDyGY26Zz2YKOD8Z3m-UwV-ljHREA"
SHEET_GID = "893494942"  # The specific sheet tab ID

# Sheet names mapping (adjust based on your actual sheet structure)
SHEET_NAMES = {
    'transactions': '消費紀錄',  # or use index 0, 1, 2, etc.
    'accounts': 'Accounts',
    'stocks': '股票投資',
    'categories': '項目分類',
    'budgets': 'Budgets'
}

def get_sheet_data_public(sheet_name: str, use_headers: bool = True) -> pd.DataFrame:
    """
    Read data from Google Sheets using public CSV export (no authentication required).
    The sheet must be shared publicly (Anyone with the link can view).
    
    Parameters
    ----------
    sheet_name : str
        Name of the sheet tab (will be URL encoded)
    use_headers : bool
        Whether first row contains headers
    
    Returns
    -------
    pd.DataFrame
        DataFrame with sheet data
    """
    try:
        import urllib.parse
        # URL encode the sheet name
        encoded_sheet_name = urllib.parse.quote(sheet_name)
        
        # Construct CSV export URL
        # Format: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"
        
        # Read CSV directly into pandas
        df = pd.read_csv(csv_url)
        
        if df.empty:
            return pd.DataFrame()
        
        # Clean up empty rows
        df = df.dropna(how='all')
        
        return df
    except Exception as e:
        print(f"Error reading public sheet '{sheet_name}': {e}")
        return pd.DataFrame()

def get_sheet_client():
    """
    Get Google Sheets client using gspread (requires authentication). 
    Tries service account first.
    """
    if not GSPREAD_AVAILABLE:
        raise Exception("gspread is not installed. Install with: pip install gspread google-auth")
    
    # Try to use service account credentials from file
    creds_paths = [
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        'credentials.json',
        os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    ]
    
    for creds_path in creds_paths:
        if creds_path and os.path.exists(creds_path):
            try:
                scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
                creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
                return gspread.authorize(creds)
            except Exception as e:
                print(f"Service account auth failed with {creds_path}: {e}")
                continue
    
    # Try service_account() which looks for credentials in default locations
    try:
        return gspread.service_account()
    except Exception as e:
        print(f"Service account default auth failed: {e}")
    
    # For public sheets, we can use a different approach
    # Note: The sheet must be shared publicly (Anyone with the link can view)
    raise Exception("Unable to authenticate with Google Sheets. Please either:\n"
                  "1. Place a service account credentials.json file in the project root\n"
                  "2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable\n"
                  "3. Share the Google Sheet publicly and use the public URL method")

def get_sheet_data(sheet_name: str, use_headers: bool = True, use_public: bool = True) -> pd.DataFrame:
    """
    Read data from a specific sheet tab.
    Tries public CSV method first (no auth), then falls back to gspread (requires auth).
    
    Parameters
    ----------
    sheet_name : str
        Name of the sheet tab or index
    use_headers : bool
        Whether first row contains headers
    use_public : bool
        Try public CSV method first (default: True)
    
    Returns
    -------
    pd.DataFrame
        DataFrame with sheet data
    """
    # Try public CSV method first (no authentication required)
    if use_public:
        try:
            df = get_sheet_data_public(sheet_name, use_headers)
            if not df.empty:
                return df
        except Exception as e:
            print(f"Public CSV method failed, trying authenticated method: {e}")
    
    # Fallback to authenticated gspread method
    if GSPREAD_AVAILABLE:
        try:
            client = get_sheet_client()
            
            # Open the spreadsheet
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            
            # Get the specific sheet
            worksheet = None
            try:
                # Try by name first
                worksheet = spreadsheet.worksheet(sheet_name)
            except:
                # Try by index if name fails
                try:
                    worksheet = spreadsheet.get_worksheet(int(sheet_name))
                except:
                    # Try by gid if available
                    try:
                        worksheet = spreadsheet.worksheet_by_id(int(SHEET_GID))
                    except:
                        # Fallback: get first worksheet
                        worksheet = spreadsheet.sheet1
            
            if worksheet is None:
                return pd.DataFrame()
            
            # Get all values
            data = worksheet.get_all_values()
            
            if not data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            if use_headers and len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                df = pd.DataFrame(data)
            
            # Clean up empty rows
            df = df.dropna(how='all')
            
            return df
        
        except Exception as e:
            print(f"Error reading sheet '{sheet_name}' with gspread: {e}")
            import traceback
            traceback.print_exc()
    
    # If both methods fail, return empty DataFrame
    return pd.DataFrame()

def get_transactions_sheet() -> pd.DataFrame:
    """Get transactions data from Google Sheets."""
    df = get_sheet_data(SHEET_NAMES.get('transactions', 'Transactions'))
    
    if df.empty:
        return df
    
    # Ensure required columns exist and map to expected format
    # Expected columns: id, date, type, category, amount, payment_method, description, account_id, account_name
    required_cols = ['date', 'type', 'category', 'amount']
    
    # Check if columns exist (case-insensitive)
    df.columns = df.columns.str.strip()
    
    # Map common column name variations
    column_mapping = {
        '日期': 'date',
        'Date': 'date',
        '類型': 'type',
        'Type': 'type',
        '類別': 'category',
        'Category': 'category',
        '金額': 'amount',
        'Amount': 'amount',
        '支付方式': 'payment_method',
        'Payment Method': 'payment_method',
        '備註': 'description',
        'Description': 'description',
        '帳戶': 'account_name',
        'Account': 'account_name',
        '帳戶ID': 'account_id',
        'Account ID': 'account_id'
    }
    
    # Rename columns if needed
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Ensure date is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Ensure amount is numeric
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    # Add id if missing
    if 'id' not in df.columns:
        df.insert(0, 'id', range(1, len(df) + 1))
    
    return df

def get_accounts_sheet() -> pd.DataFrame:
    """Get accounts data from Google Sheets."""
    df = get_sheet_data(SHEET_NAMES.get('accounts', 'Accounts'))
    
    if df.empty:
        return df
    
    # Map columns
    column_mapping = {
        '名稱': 'name',
        'Name': 'name',
        '類型': 'type',
        'Type': 'type',
        '初始餘額': 'initial_balance',
        'Initial Balance': 'initial_balance'
    }
    
    df.columns = df.columns.str.strip()
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Add id if missing
    if 'id' not in df.columns:
        df.insert(0, 'id', range(1, len(df) + 1))
    
    # Ensure initial_balance is numeric
    if 'initial_balance' in df.columns:
        df['initial_balance'] = pd.to_numeric(df['initial_balance'], errors='coerce').fillna(0)
    
    return df

def get_stocks_sheet() -> pd.DataFrame:
    """Get stocks data from Google Sheets."""
    df = get_sheet_data(SHEET_NAMES.get('stocks', 'Stocks'))
    
    if df.empty:
        return df
    
    # Map columns
    column_mapping = {
        '代號': 'symbol',
        'Symbol': 'symbol',
        '購買日期': 'buy_date',
        'Buy Date': 'buy_date',
        '買入價格': 'buy_price',
        'Buy Price': 'buy_price',
        '數量': 'quantity',
        'Quantity': 'quantity',
        '手續費': 'broker_fee',
        'Broker Fee': 'broker_fee',
        '交易費': 'transaction_fee',
        'Transaction Fee': 'transaction_fee',
        '狀態': 'status',
        'Status': 'status'
    }
    
    df.columns = df.columns.str.strip()
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Add id if missing
    if 'id' not in df.columns:
        df.insert(0, 'id', range(1, len(df) + 1))
    
    # Ensure numeric columns
    numeric_cols = ['buy_price', 'quantity', 'broker_fee', 'transaction_fee']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Filter by status if exists
    if 'status' in df.columns:
        df = df[df['status'].str.upper().isin(['HELD', '持有', '']) | df['status'].isna()]
    
    return df

def get_categories_sheet() -> pd.DataFrame:
    """Get categories data from Google Sheets."""
    df = get_sheet_data(SHEET_NAMES.get('categories', 'Categories'))
    
    if df.empty:
        return df
    
    # Map columns
    column_mapping = {
        '名稱': 'name',
        'Name': 'name',
        '類型': 'type',
        'Type': 'type'
    }
    
    df.columns = df.columns.str.strip()
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Add id if missing
    if 'id' not in df.columns:
        df.insert(0, 'id', range(1, len(df) + 1))
    
    return df

def get_budgets_sheet() -> pd.DataFrame:
    """Get budgets data from Google Sheets."""
    df = get_sheet_data(SHEET_NAMES.get('budgets', 'Budgets'))
    
    if df.empty:
        return df
    
    # Map columns
    column_mapping = {
        '月份': 'month',
        'Month': 'month',
        '金額': 'amount',
        'Amount': 'amount'
    }
    
    df.columns = df.columns.str.strip()
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Ensure amount is numeric
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    return df

