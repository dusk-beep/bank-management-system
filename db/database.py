from enum import Enum

import mariadb


class transaction_type(Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class Database:
    def __init__(self, db_info: dict[str, str]) -> None:
        try:
            self.conn = mariadb.connect(
                user=db_info["user"],
                host=db_info["host"],
                port=int(db_info["port"]),
                database=db_info["database"],
            )
            print("succesfully connected to database")
            self.setup_data()
        except mariadb.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def setup_data(self) -> None:
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Users (
                        user_id INT PRIMARY KEY AUTO_INCREMENT,
                        Name varchar(255),
                        Email Varchar(255) UNIQUE,
                        Created_at timestamp default current_timestamp
                    )
            """)

            cursor.execute("""
                    Create table if not EXISTS Accounts (
                    acc_no int primary key AUTO_INCREMENT,
                    user_id int,
                    acc_type enum('savings','current'),
                    balance Decimal(10,2),
                    start_date Date,

                    foreign key(user_id) REFERENCES Users(user_id)
                    )
            """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Transactions (
                        transaction_id INT PRIMARY KEY AUTO_INCREMENT,
                        amount DECIMAL(10, 2),
                        transaction_Type ENUM('credit', 'debit'),
                        created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        acc_no INT,
                        FOREIGN KEY(acc_no) REFERENCES Accounts(acc_no)
                    )
                    """)
            self.conn.commit()
            print("database setup completed")
        except mariadb.Error as e:
            print(f"Error setting up data: {e}")

    def insert_users(self, users):
        try:
            cursor = self.conn.cursor()
            cursor.executemany("INSERT INTO Users (name, email) VALUES (?, ?)", users)
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error inserting users: {e}")

    def insert_accounts(self, accounts):
        try:
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT INTO Accounts (user_id, acc_type, balance, start_date) VALUES (?, ?, ?, ?)",
                accounts,
            )
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error inserting accounts: {e}")

    def insert_transactions(self, transactions):
        try:
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT INTO Transactions (amount, transaction_type, user_id, acc_no) VALUES (?, ?, ?, ?)",
                transactions,
            )
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error inserting transactions: {e}")

    def execute_query(self, query, params=None):
        try:
            cursor = self.conn.cursor()  # Use a local cursor for execution
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()  # Fetch the result
            cursor.close()  # Close the local cursor
            return result
        except mariadb.Error as e:
            print(f"Database error: {e}")
            return None

    def retrieve_user_info(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "select Name,email,created_At,acc_type,balance from Users natural join Accounts"
            )
            return cursor.fetchone()
        except mariadb.Error as e:
            print(f"Error inserting transactions: {e}")
        finally:
            cursor.close()

    def check_account_exist(self, account_no):
        query = "select acc_no from Accounts where acc_no = ?"
        res = self.execute_query(query=query, params=(account_no,))
        if not res:
            return False
        return True

    def setTransactions(self, account_no, amount, type):
        try:
            cursor = self.conn.cursor()
            query = "insert into Transactions (acc_no,amount,transaction_type) values (?,?,?)"
            cursor.execute(query, (account_no, amount, type))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error setTransactions: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def getTransactions(self, user_id):
        try:
            cursor = self.conn.cursor()
            query = "select acc_no,created_At,amount,transaction_type from Transactions natural join Accounts where user_id=?"
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error kn credit opertion: {e}")
            self.conn.rollback()
            return []
        finally:
            cursor.close()

    def debit(self, account_no, amount):
        try:
            cursor = self.conn.cursor()
            # TODO check min balance
            query = "update Accounts set balance = balance - ? where acc_no =?"
            cursor.execute(query, (amount, account_no))
            self.setTransactions(account_no, amount, transaction_type.DEBIT.value)
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error in debit opertion: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def credit(self, account_no, amount):
        try:
            cursor = self.conn.cursor()
            query = "update Accounts set balance = balance + ? where acc_no =?"
            cursor.execute(query, (amount, account_no))
            print(f"inserted {amount} into {account_no}")
            self.setTransactions(account_no, amount, transaction_type.CREDIT.value)
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error in credit opertion: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def get_accounts(self, user_id):
        try:
            cursor = self.conn.cursor()
            query = "select acc_no from Accounts where user_id = ?"
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error getting account numbers: {e}")
        finally:
            cursor.close()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
