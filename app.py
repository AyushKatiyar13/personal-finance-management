import sqlite3
from fpdf import FPDF
import hashlib
import re
from datetime import datetime, timedelta
from database import (
    register_user,
    authenticate_user,
    add_transaction,
    view_transactions,
    delete_transaction,
    get_report,
    set_budget,
    get_budget,
    get_total_expenses,
    create_tables,
    create_budget_table,
    backup_data,
    generate_backup_pdf  # Ensure this is imported
)

# Function to set or update the budget for a user
def set_user_budget(user_id):
    """
    Allows the user to set or update their budget for a specific category or overall budget.
    
    Args:
        user_id (int): The unique ID of the user whose budget is being set or updated.
    
    Returns:
        None
    """
    print("\n--- Set or Update Budget ---")
    category = input("Enter budget category (e.g., Food, Rent, or 'total' for overall budget): ")
    amount = float(input(f"Enter the amount for the {category} budget: "))
    period = input("Enter the period ('monthly' or 'yearly'): ").lower()

    # Set or update the budget in the database
    set_budget(user_id, category, amount, period)
    print(f"Budget for {category} in {period} set to {amount}.")

# Function to view the user's budget and expenses comparison
def view_budget(user_id, period='monthly'):
    """
    Views the user's budget and checks for any budget exceedance by comparing the budget 
    with total expenses for each category in the given period.
    
    Args:
        user_id (int): The unique ID of the user.
        period (str): The period for which to view the budget ('monthly' or 'yearly'). Default is 'monthly'.
    
    Returns:
        None
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()

    # Fetch all budgets for the user for the specified period
    cursor.execute("SELECT category, amount FROM budgets WHERE user_id = ? AND period = ?", (user_id, period))
    budgets = cursor.fetchall()

    print(f"\n--- Budget for {period} ---")
    
    budget_exceedance_found = False  # Track if any budget exceedance occurred

    # Check each budget category
    for budget in budgets:
        category, budget_amount = budget
        # Fetch total expenses for each category in the specified period
        cursor.execute('''SELECT SUM(amount) FROM transactions 
                          WHERE user_id = ? AND category = ? AND type = 'expense' AND date LIKE ?''',
                       (user_id, category, f"{datetime.now().year}-{datetime.now().month:02d}%" if period == 'monthly' else f"{datetime.now().year}%"))
        total_expenses = cursor.fetchone()[0] or 0  # Default to 0 if no expenses

        print(f"Category: {category}, Budget: {budget_amount}, Total Expenses: {total_expenses}")

        # Check if expenses exceed the budget for each category
        if total_expenses > budget_amount:
            print(f"Warning: You have exceeded your budget for {category}!")
            budget_exceedance_found = True

    if not budget_exceedance_found:
        print("You are within your budget for all categories.")

    conn.close()

# Function to connect to the database
def create_connection(db_file='finance.db'):
    """
    Creates a connection to the SQLite database.
    
    Args:
        db_file (str): The name of the database file (default is 'finance.db').
    
    Returns:
        sqlite3.Connection: The database connection object.
    """
    conn = sqlite3.connect(db_file)
    return conn

# Function to validate the username format
def validate_username(username):
    """
    Validates the username format. The username should start with an alphabet and can
    contain alphanumeric characters or underscores.
    
    Args:
        username (str): The username to validate.
    
    Returns:
        bool: True if the username is valid, False otherwise.
    """
    if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return True
    else:
        return False

# Function to validate the password length
def validate_password(password):
    """
    Validates the password length. The password should be at least 4 characters long.
    
    Args:
        password (str): The password to validate.
    
    Returns:
        bool: True if the password is valid, False otherwise.
    """
    return len(password) >= 4

# Function to register a new user
def register_user(username, password):
    """
    Registers a new user by validating their username and password, and storing the user's 
    data in the database.
    
    Args:
        username (str): The chosen username for the new user.
        password (str): The chosen password for the new user.
    
    Returns:
        bool: True if the registration is successful, False otherwise.
    """
    if not validate_username(username):
        print("Invalid username! It should start with an alphabet and can contain numbers and special characters.")
        return False
    
    if not validate_password(password):
        print("Invalid password! Password should be at least 4 characters long.")
        return False

    conn = create_connection()
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print("Username already exists!")
        conn.close()
        return False

    # Hash the password before storing
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Insert the new user into the database
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()
    print(f"User {username} registered successfully!")
    return True

# Function to authenticate a user during login
def authenticate_user(username, password):
    """
    Authenticates a user by comparing the entered password with the stored hashed password.
    
    Args:
        username (str): The username of the user attempting to log in.
        password (str): The password entered by the user.
    
    Returns:
        int or None: The user ID if authentication is successful, None otherwise.
    """
    conn = create_connection()
    cursor = conn.cursor()

    # Fetch user from database
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        # Compare hashed password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if hashed_password == user[2]:  # user[2] is the password field in the DB
            print(f"User {username} logged in successfully!")
            return user[0]  # Return user ID
        else:
            print("Invalid password!")
            return None
    else:
        print("Username not found!")
        return None

# Function to generate a financial report (income vs expense)
def get_report(user_id, period='monthly'):
    """
    Generates a financial report showing total income, total expenses, and savings for 
    a specified period (monthly or yearly).
    
    Args:
        user_id (int): The unique ID of the user for whom the report is generated.
        period (str): The period for the report ('monthly' or 'yearly'). Default is 'monthly'.
    
    Returns:
        dict: A dictionary containing income, expense, savings, start date, and end date for the report.
    """
    conn = create_connection('finance.db')
    cursor = conn.cursor()
    
    # Get current month and year for report filtering
    current_date = datetime.now()
    if period == 'monthly':
        start_date = current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
    elif period == 'yearly':
        start_date = f"{current_date.year}-01-01"
        end_date = f"{current_date.year}-12-31"
    else:
        raise ValueError("Period must be 'monthly' or 'yearly'")

    # Fetch transactions within the specified period
    cursor.execute('''SELECT SUM(amount), type FROM transactions
                      WHERE user_id = ? AND date BETWEEN ? AND ? 
                      GROUP BY type''', (user_id, start_date, end_date))

    transactions = cursor.fetchall()
    income = 0
    expense = 0

    for transaction in transactions:
        if transaction[1] == 'income':
            income = transaction[0] if transaction[0] else 0
        elif transaction[1] == 'expense':
            expense = transaction[0] if transaction[0] else 0

    savings = income - expense
    conn.close()

    return {
        'income': income,
        'expense': expense,
        'savings': savings,
        'start_date': start_date,
        'end_date': end_date
    }

def delete_transaction(conn, user_id, transaction_id):
    """ 
    Delete a transaction from the database by its ID and user ID.
    
    Args:
        conn (sqlite3.Connection): Database connection.
        user_id (int): The ID of the user who owns the transaction.
        transaction_id (int): The ID of the transaction to delete.
    """
    cursor = conn.cursor()

    # Check if the transaction belongs to the user
    cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    transaction = cursor.fetchone()

    if transaction:
        # Delete the transaction if it belongs to the user
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        print(f"Transaction {transaction_id} deleted successfully!")
    else:
        print("Transaction not found or you do not have permission to delete it.")


# Main function to handle user input for registration and login
def main():
    """
    The main function that allows a user to register, log in, or exit the application. 
    If logged in successfully, the main menu is displayed.
    
    Returns:
        None
    """
    user_id = None

    while True:
        action = input("Do you want to (register/login/exit): ").lower()
        
        if action == "register":
            username = input("Enter username: ")
            password = input("Enter password: ")
            register_user(username, password)

        elif action == "login":
            username = input("Enter username: ")
            password = input("Enter password: ")
            user_id = authenticate_user(username, password)

            if user_id:
                main_menu(user_id)  # Call main menu with user ID after successful login
                break

        elif action == "exit":
            print("Exiting...")
            break
        
        else:
            print("Invalid option, please choose 'register', 'login', or 'exit'.")

# Update the main menu to include Budget options
def main_menu(user_id):
    if user_id is None:
        print("Error: User ID is None. Please login first.")
        return
    conn = create_connection('finance.db')  # Create a database connection
    
    while True:
        print("\n--- Transaction Options ---")
        print("1. Add Income")
        print("2. Add Expense")
        print("3. View Transactions")
        print("4. Delete Transaction")
        print("5. View Financial Report")
        print("6. Set/Update Budget")
        print("7. View Budget")
        print("8. Backup Database")
        print("9. Logout")
        
        choice = input("Choose an option: ")

        if choice == '1':  # Add Income
            amount = float(input("Enter income amount: "))
            description = input("Enter description: ")
            category = input("Enter category (e.g., Salary, Business): ")
            add_transaction(conn, user_id, 'income', amount, description, category)  # Pass conn
            conn.commit()  # Ensure changes are committed

        elif choice == '2':  # Add Expense
            amount = float(input("Enter expense amount: "))
            description = input("Enter description: ")
            category = input("Enter category (e.g., Food, Rent): ")
            add_transaction(conn, user_id, 'expense', amount, description, category)  # Pass conn
            conn.commit()  # Ensure changes are committed

        elif choice == '3':  # View Transactions
            # print(f"User ID is {user_id}")  # Debugging line
            view_transactions(conn, user_id)  # Pass both conn and user_id

        elif choice == '4':  # Delete Transaction
            transaction_id = int(input("Enter transaction ID to delete: "))
            delete_transaction(conn, user_id, transaction_id)  # Pass conn and user_id

        elif choice == '5':  # View Financial Report
            period = input("Enter period ('monthly' or 'yearly'): ").lower()
            report = get_report(user_id, period)
            print(report)

        elif choice == '6':  # Set/Update Budget
            set_user_budget(user_id)

        elif choice == '7':  # View Budget
            view_budget(user_id)

        elif choice == '8':  # Backup Database
            generate_backup_pdf()  # Call the PDF backup function

        elif choice == '9':  # Logout
            print("Logging out...")
            break

        else:
            print("Invalid choice, please try again.")
    
    conn.close()  # Close the connection after the operation


# Start the main function
if __name__ == '__main__':
    create_tables()  # Ensure tables are created
    create_budget_table()  # Ensure budget table exists
    main()
