class Transaction:
    """
    Represents a financial transaction, which could be an income or an expense.

    Attributes:
        transaction_type (str): Type of the transaction, either 'income' or 'expense'.
        amount (float): The amount of money involved in the transaction.
        category (str): The category for the transaction (e.g., 'Food', 'Salary').
        description (str): A brief description of the transaction.
    """

    def __init__(self, transaction_type, amount, category, description):
        """
        Initializes a new transaction instance with the provided details.

        Args:
            transaction_type (str): Type of the transaction, 'income' or 'expense'.
            amount (float): The amount of money involved in the transaction.
            category (str): The category to which the transaction belongs.
            description (str): A short description of the transaction.

        Example:
            transaction = Transaction('income', 5000, 'Salary', 'Monthly salary payment')
        """
        self.transaction_type = transaction_type  # 'income' or 'expense'
        self.amount = amount  # The amount of money for the transaction
        self.category = category  # The category of the transaction (e.g., 'Food', 'Salary')
        self.description = description  # A brief description of the transaction
