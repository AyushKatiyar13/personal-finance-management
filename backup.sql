# SQL commands to create the 'users' table and insert sample data

# Dumping the schema of the 'users' table
# This SQL statement creates a table named 'users' with three columns:
# - id: An integer that auto-increments and serves as the primary key.
# - username: A text field to store the user's unique name.
# - password: A text field to store the user's password.
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  # Automatically increments for each new user
    username TEXT NOT NULL UNIQUE,  # Ensures each username is unique
    password TEXT NOT NULL  # Ensures password is always provided
);

# Dumping the data in the 'users' table
# These SQL statements insert two users into the 'users' table with their respective usernames and passwords.
INSERT INTO users (id, username, password) VALUES (1, 'user1', 'password1');
INSERT INTO users (id, username, password) VALUES (2, 'user2', 'password2');
# More similar INSERT statements for other tables can be added as needed

# Entry point of the script. This block will only run if the script is executed directly
if __name__ == "__main__":  
    # Remove or comment out the old SQL backup code if not needed anymore
    # backup_data()  # This line is for the old method that created the .sql file backup

    # Call the function to generate the PDF backup
    # This line will generate a backup of the database in PDF format.
    generate_backup_pdf()  # This function will create a backup in a PDF file format
