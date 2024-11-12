import unittest
from database import register_user, create_connection, authenticate_user, add_transaction, view_transactions  # Import the functions to be tested

# Base class to set up the test database
class BaseTestCase(unittest.TestCase):
    """
    Base test case class that sets up an in-memory SQLite database 
    for testing the functions in the database module.
    """
    def setUp(self):
        """
        Set up the test environment before each test.
        This creates an in-memory database and creates the necessary tables 
        for users and transactions.
        """
        # Use an in-memory database to avoid modifying the real database
        self.db_connection = create_connection(':memory:')
        self.cursor = self.db_connection.cursor()

        # Create the users table for each test
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT NOT NULL UNIQUE,
                                password TEXT NOT NULL
                            )''')

        # Create the transactions table for each test
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER,
                                amount REAL,
                                category TEXT,
                                type TEXT,
                                FOREIGN KEY (user_id) REFERENCES users (id)
                            )''')

        # Commit the changes to the in-memory database
        self.db_connection.commit()

    def tearDown(self):
        """
        Clean up the test environment after each test.
        Closes the in-memory database connection.
        """
        # Close the in-memory connection after each test
        self.db_connection.close()

class TestUserFunctions(BaseTestCase):
    """
    Test case class for testing user-related functions: registration.
    """

    def test_register_user_success(self):
        """
        Test successful user registration.
        Registers a new user and checks if the registration is successful.
        """
        result = register_user(self.db_connection, 'testuser', 'password123')
        self.assertEqual(result, 'User registered successfully!')  # Expect success message

    def test_register_user_existing_user(self):
        """
        Test user registration with an existing username.
        Tries to register a user with the same username twice and checks 
        if the system returns the 'Username already exists!' message.
        """
        register_user(self.db_connection, 'testuser', 'password123')  # First registration
        result = register_user(self.db_connection, 'testuser', 'password123')  # Second registration with same username
        self.assertEqual(result, 'Username already exists!')  # Expect error message

class TestAuthentication(BaseTestCase):
    """
    Test case class for testing user authentication.
    """

    def test_authenticate_user_success(self):
        """
        Test successful user authentication.
        Registers a user and authenticates with correct credentials, 
        expecting a valid user_id in return.
        """
        register_user(self.db_connection, 'user1', 'password1')  # Register a user
        user_id = authenticate_user(self.db_connection, 'user1', 'password1')  # Authenticate with correct credentials
        self.assertIsNotNone(user_id)  # Should return a user_id (not None)

    def test_authenticate_user_failure(self):
        """
        Test user authentication with incorrect credentials.
        Tries to authenticate with incorrect username/password and expects 
        a None return value.
        """
        user_id = authenticate_user(self.db_connection, 'wrong_user', 'wrong_password')  # Authenticate with wrong credentials
        self.assertIsNone(user_id)  # Should return None for failed authentication

class TestTransactionFunctions(BaseTestCase):
    """
    Test case class for testing transaction-related functions: adding transactions.
    """

    def test_add_transaction(self):
        """
        Test adding a transaction.
        Registers a user, adds a transaction, and then verifies if the transaction 
        was successfully added by checking the transaction details.
        """
        register_user(self.db_connection, 'user2', 'password2')  # Register a new user
        add_transaction(self.db_connection, 'user2', 100, 'Food', 'expense')  # Add a transaction for 'user2'
        transactions = view_transactions(self.db_connection, 'user2')  # Retrieve the transactions for 'user2'
        self.assertEqual(len(transactions), 1)  # Should have exactly 1 transaction
        self.assertEqual(transactions[0][0], 100)  # Amount should be 100 (index 0 for amount)

# Run the tests
if __name__ == "__main__":
    unittest.main()
