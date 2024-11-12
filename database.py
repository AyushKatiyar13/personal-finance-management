import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

db_connection = sqlite3.connect('finance.db')  # This should establish a connection to the database

# Function to create a database connection
def create_connection(db_file):
    """ 
    Create a database connection to a SQLite database.
    
    Args:
        db_file (str): The database file path.

    Returns:
        conn (sqlite3.Connection): SQLite database connection object.
    """
    conn = sqlite3.connect(db_file)
    return conn

# Function to generate financial report
def get_report(user_id, period='monthly'):
    """ 
    Generate a financial report for the given user and period ('monthly' or 'yearly').
    
    Args:
        user_id (int): The user ID for whom the report is generated.
        period (str): The period for the report, either 'monthly' or 'yearly'. Default is 'monthly'.
        
    Returns:
        dict: A dictionary containing income, expense, savings, and the date range for the report.
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Get the current date for filtering the report
    current_date = datetime.now()

    # Set the start and end dates based on the period
    if period == 'monthly':
        start_date = f"{current_date.year}-{current_date.month:02d}-01"
        end_date = f"{current_date.year}-{current_date.month:02d}-{current_date.day:02d}"
    elif period == 'yearly':
        start_date = f"{current_date.year}-01-01"
        end_date = f"{current_date.year}-12-31"
    else:
        raise ValueError("Period must be 'monthly' or 'yearly'")

    # Fetch transactions for the specified period
    cursor.execute('''SELECT SUM(amount), type FROM transactions
                      WHERE user_id = ? AND date BETWEEN ? AND ?
                      GROUP BY type''', (user_id, start_date, end_date))

    transactions = cursor.fetchall()
    income, expense = 0, 0

    # Categorize income and expense
    for transaction in transactions:
        if transaction[1] == 'income':
            income = transaction[0] or 0
        elif transaction[1] == 'expense':
            expense = transaction[0] or 0

    savings = income - expense
    conn.close()

    # Return the financial report as a dictionary
    return {
        'income': income,
        'expense': expense,
        'savings': savings,
        'start_date': start_date,
        'end_date': end_date
    }

# Function to create tables for users and transactions
def create_tables():
    """ 
    Create the necessary tables for users and transactions in the database.
    
    This function checks if the 'users' and 'transactions' tables exist, and if not, creates them.
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Create table for Users
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )''')

    # Create table for Transactions (Income/Expense)
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        amount REAL,
                        category TEXT,
                        type TEXT,  -- 'income' or 'expense'
                        date TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

    conn.commit()
    conn.close()

# Function to register a new user
def register_user(conn, username, password):
    """
    Register a new user by inserting their username and password into the database.
    
    Args:
        conn (sqlite3.Connection): Database connection.
        username (str): The username of the new user.
        password (str): The password for the new user.

    Returns:
        str: A message indicating the result of the registration (success or error).
    """
    cursor = conn.cursor()

    # Check if the user already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        return 'Username already exists!'

    # Insert new user into the users table
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    return 'User registered successfully!'

# Function to authenticate a user
def authenticate_user(username, password):
    """ 
    Authenticate a user by checking if the provided username and password match an existing user.
    
    Args:
        username (str): The username provided by the user.
        password (str): The password provided by the user.

    Returns:
        int or None: The user ID if authentication is successful, otherwise None.
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Check if the user exists and if the password matches
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return user[0]  # Return user_id if authentication is successful
    else:
        return None  # Authentication failed

def add_transaction(db_connection, user_id, transaction_type, amount, description, category):
    """ 
    Add a new transaction (income or expense) to the database for a specified user.
    
    Args:
        db_connection (sqlite3.Connection): Database connection.
        user_id (int): The user ID of the user adding the transaction.
        amount (float): The amount of the transaction.
        category (str): The category of the transaction (e.g., 'food', 'salary').
        transaction_type (str): The type of transaction ('income' or 'expense').
    """
    cursor = db_connection.cursor()
    
    # Insert the transaction using user_id instead of username
    cursor.execute('''INSERT INTO transactions (user_id, amount, category, type) 
                      VALUES (?, ?, ?, ?)''', (user_id, amount, category, transaction_type))
    db_connection.commit()

def view_transactions(db_connection, user_id):
    """ 
    View all transactions (income or expense) for a specified user.
    
    Args:
        db_connection (sqlite3.Connection): Database connection.
        user_id (int): The user ID whose transactions are to be viewed.
        
    Returns:
        list: A list of transactions for the user, including amount, category, and type.
    """
    cursor = db_connection.cursor()
    cursor.execute("SELECT id, amount, category, type, date FROM transactions WHERE user_id = ?", (user_id,))
    transactions = cursor.fetchall()

    if not transactions:
        print("No transactions found for this user.")
    else:
        print("\n--- Transactions ---")
        for transaction in transactions:
            print(f"ID: {transaction[0]}, Amount: {transaction[1]}, Category: {transaction[2]}, Type: {transaction[3]}, Date: {transaction[4]}")

    return transactions  # Returning the list for further use (if needed)


def delete_transaction(db_connection, transaction_id, user_id):
    """ 
    Delete a transaction from the database by its ID, ensuring the user owns the transaction.
    
    Args:
        transaction_id (int): The ID of the transaction to delete.
        user_id (int): The ID of the logged-in user.
    """
    cursor = db_connection.cursor()

    # Check if the transaction exists and if the user is the owner
    cursor.execute("SELECT user_id FROM transactions WHERE id = ?", (transaction_id,))
    transaction = cursor.fetchone()

    if transaction and transaction[0] == user_id:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        db_connection.commit()
        print(f"Transaction {transaction_id} deleted successfully.")
    else:
        print("Transaction not found or you do not have permission to delete it.")


def update_transaction(transaction_id, amount, category, transaction_type):
    """ 
    Update the details of an existing transaction.
    
    Args:
        transaction_id (int): The ID of the transaction to update.
        amount (float): The new amount for the transaction.
        category (str): The new category for the transaction.
        transaction_type (str): The new type of transaction ('income' or 'expense').
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Update the transaction details in the database
    cursor.execute('''UPDATE transactions SET amount = ?, category = ?, type = ? WHERE id = ?''',
                   (amount, category, transaction_type, transaction_id))
    conn.commit()
    conn.close()

# Function to create a table for budgets
def create_budget_table():
    """
    Create a table for budgets in the database.

    This table stores budget information for different categories and periods (monthly or yearly) for each user.
    If the table already exists, it will not be created again.

    Returns:
        None
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Create table for Budgets if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        category TEXT,
                        amount REAL,
                        period TEXT,  -- 'monthly' or 'yearly'
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

    conn.commit()
    conn.close()

# Function to set or update a user's budget
def set_budget(user_id, category, amount, period='monthly'):
    """
    Set or update a budget for a specific category and period.

    Parameters:
        user_id (int): The ID of the user.
        category (str): The budget category (e.g., 'food', 'transport').
        amount (float): The budget amount.
        period (str): The budget period ('monthly' or 'yearly'). Default is 'monthly'.

    Returns:
        None
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Check if the user already has a budget for the given category and period
    cursor.execute('''SELECT * FROM budgets WHERE user_id = ? AND category = ? AND period = ?''', 
                   (user_id, category, period))
    existing_budget = cursor.fetchone()

    if existing_budget:
        # Update the existing budget
        cursor.execute('''UPDATE budgets SET amount = ? WHERE user_id = ? AND category = ? AND period = ?''',
                       (amount, user_id, category, period))
    else:
        # Insert a new budget
        cursor.execute('''INSERT INTO budgets (user_id, category, amount, period)
                          VALUES (?, ?, ?, ?)''', (user_id, category, amount, period))
    
    conn.commit()
    conn.close()

# Function to get a user's budget for a specific period
def get_budget(user_id, period='monthly'):
    """
    Get all budgets for a user in a specific period.

    Parameters:
        user_id (int): The ID of the user.
        period (str): The budget period ('monthly' or 'yearly'). Default is 'monthly'.

    Returns:
        list: A list of tuples, each containing a budget category and amount.
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    cursor.execute('''SELECT category, amount FROM budgets WHERE user_id = ? AND period = ?''',
                   (user_id, period))
    budgets = cursor.fetchall()

    conn.close()
    return budgets

# Function to fetch total expenses for a user in a specific period
def get_total_expenses(user_id, period='monthly'):
    """
    Get the total expenses for the user in a given period.

    Parameters:
        user_id (int): The ID of the user.
        period (str): The period for calculating expenses ('monthly' or 'yearly'). Default is 'monthly'.

    Returns:
        float: The total amount of expenses in the given period.
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    current_date = datetime.now()
    if period == 'monthly':
        start_date = current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
    elif period == 'yearly':
        start_date = f"{current_date.year}-01-01"
        end_date = f"{current_date.year}-12-31"
    
    # Fetch total expenses within the period
    cursor.execute('''SELECT SUM(amount) FROM transactions
                      WHERE user_id = ? AND type = 'expense' AND date BETWEEN ? AND ?''', 
                   (user_id, start_date, end_date))
    total_expenses = cursor.fetchone()[0] or 0  # Default to 0 if None

    conn.close()
    return total_expenses

def backup_data():
    """
    Backup the database to a specified file.
    
    Prompts the user for a file path to store the backup. If no path is provided, 
    a default file name 'backup.sql' is used.
    
    Returns:
        None
    """
    backup_file = input("Enter the file path for backup (default: backup.sql): ") or "backup.sql"
    try:
        conn = create_connection('finance.db')
        with open(backup_file, 'w') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        print(f"Database backup successful! Backup file: {backup_file}")
    except Exception as e:
        print(f"Failed to create backup: {e}")
    finally:
        if conn:
            conn.close()

# Function to generate a PDF of the database backup
def generate_backup_pdf():
    """
    Generate a PDF report of the database backup, including user and transaction data.

    This function creates a PDF file containing the contents of the 'users' and 'transactions' 
    tables from the database, which serves as a report for the backup.

    Returns:
        None
    """
    # Create a new PDF file
    filename = "database_backup.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Set up some initial settings for the PDF
    c.setFont("Helvetica", 10)
    width, height = letter  # Page size
    
    # Title for the PDF
    c.drawString(200, height - 40, "Database Backup Report")
    
    # Write the Users Data
    c.drawString(40, height - 80, "Users Table:")
    y_position = height - 100  # Starting Y position for user data
    
    # Connect to the database
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Get all users
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    # Write each user's data to the PDF
    for user in users:
        c.drawString(40, y_position, f"ID: {user[0]}, Username: {user[1]}")
        y_position -= 15

    # Adding some space
    y_position -= 20
    c.drawString(40, y_position, "Transactions Table:")
    y_position -= 20
    
    # Get all transactions
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()

    # Write each transaction's data to the PDF
    for transaction in transactions:
        c.drawString(40, y_position, f"ID: {transaction[0]}, User ID: {transaction[1]}, Amount: {transaction[2]}, Category: {transaction[3]}, Type: {transaction[4]}, Date: {transaction[5]}")
        y_position -= 15

    # Close the connection
    conn.close()
    
    # Save the PDF
    c.save()

    print("Backup PDF generated successfully!")

# Call this function whenever you want to generate the backup PDF
if __name__ == '__main__':
    generate_backup_pdf()
    create_tables()
    create_budget_table()
