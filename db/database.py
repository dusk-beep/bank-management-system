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
                    create table if not exists Branch (
                        branch_id int primary key AUTO_INCREMENT,
                        branch_name varchar(250),
                        branch_address varchar(255),
                        ifsc_code varchar(30)
                    )
            """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Employee (
                        emp_id INT PRIMARY KEY AUTO_INCREMENT,
                        emp_name varchar(255),
                        emp_email varchar(255),
                        password varchar(255),

                        branch_id int,
                        foreign key(branch_id) REFERENCES Branch(branch_id)
                    )
                    """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Customer (
                        cust_id INT PRIMARY KEY AUTO_INCREMENT,
                        cust_name varchar(255),
                        cust_email Varchar(255) UNIQUE,
                        cust_date timestamp default current_timestamp,
                        password varchar(255)
                    )
            """)

            cursor.execute("""
                    Create table if not EXISTS Account (
                        acc_no int primary key AUTO_INCREMENT,
                        acc_type enum('savings','current'),
                        acc_balance Decimal(10,2),
                        acc_start_date timestamp default current_timestamp,
                        cust_id int,

                        foreign key(cust_id) REFERENCES Customer(cust_id)
                    )
            """)

            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Transaction (
                        transaction_id INT PRIMARY KEY AUTO_INCREMENT,
                        created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        amount DECIMAL(10, 2),
                        from_acc_no INT,
                        to_acc_no int,
                        FOREIGN KEY(from_acc_no) REFERENCES Account(acc_no),
                        FOREIGN KEY(to_acc_no) REFERENCES Account(acc_no)
                    )
                    """)

            self.conn.commit()
            print("database setup completed")
        except mariadb.Error as e:
            print(f"Error setting up data: {e}")

    def insert_branch(self, branch_name, branch_address, ifsc_code):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Branch (branch_name, branch_address,ifsc_code) VALUES (?, ?,?)",
                (branch_name, branch_address, ifsc_code),
            )
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error inserting users: {e}")
        finally:
            cursor.close()

    def insert_users(self, cust_name, cust_email, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Customer (cust_name, cust_email,password) VALUES (?, ?,?) returning cust_id",
                (
                    cust_name,
                    cust_email,
                    password,
                ),
            )
            self.conn.commit()
            return cursor.fetchone()
        except mariadb.Error as e:
            print(f"Error inserting users: {e}")
        finally:
            cursor.close()

    def insert_employee(self, emp_name, emp_email, password, branch_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Employee (branch_id,emp_name, emp_email,password) VALUES (?, ?,?,?)",
                (
                    branch_id,
                    emp_name,
                    emp_email,
                    password,
                ),
            )
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error inserting employes: {e}")
        finally:
            cursor.close()

    def insert_accounts(self, cust_id, acc_type, acc_balance):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Account (cust_id, acc_type, acc_balance) VALUES (?, ?, ?)",
                (cust_id, acc_type, acc_balance),
            )
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error inserting accounts: {e}")
        finally:
            cursor.close()

    def insert_transactions(self, amount, from_acc_no, to_acc_no):
        try:
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT INTO Transactions (amount, from_acc_no,to_acc_no) VALUES (?, ?, ?, ?)",
                (amount, from_acc_no, to_acc_no),
            )
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error inserting transactions: {e}")
        finally:
            cursor.close()

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

    def retrieve_user_info(self, cust_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "select cust_name,cust_email,cust_date,acc_type,acc_balance from Customer natural join Account where cust_id = ?",
                (cust_id,),
            )
            return cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error inserting transactions: {e}")
            return []
        finally:
            cursor.close()

    def check_account_exist(self, account_no):
        query = "select acc_no from Account where acc_no = ?"
        res = self.execute_query(query=query, params=(account_no,))
        if not res:
            return False
        return True

    def setTransactions(self, from_account_no, to_acc_no, amount):
        try:
            cursor = self.conn.cursor()
            query = (
                "insert into Transaction (from_acc_no,to_acc_no,amount) values (?,?,?)"
            )
            cursor.execute(query, (from_account_no, to_acc_no, amount))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error setTransactions: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def getTransactions(self, cust_id):
        try:
            cursor = self.conn.cursor()
            query = "select * from Transaction where from_acc_no = ? or to_acc_no = ?"
            cursor.execute(query, (cust_id, cust_id))
            results = cursor.fetchall()
            transactions = [
                {
                    "trans_id": row[0],
                    "date": row[1],
                    "amount": row[2],
                    "from_acc_no": row[3],
                    "to_acc_no": row[4],
                }
                for row in results
            ]
        except mariadb.Error as e:
            print(f"Error kn credit opertion: {e}")
            self.conn.rollback()
            return []
        finally:
            cursor.close()

        return transactions

    def minimum(self, account_no) -> bool:
        try:
            cursor = self.conn.cursor()
            query = "select acc_balance from Account where acc_num =?"
            cursor.execute(query, (account_no,))
            balance = int(cursor.fetchall()[0])

            if balance > 500:
                return True
            else:
                return False
        except mariadb.Error as e:
            print(f"Error kn credit opertion: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()

    def debit(self, account_no, amount):
        try:
            cursor = self.conn.cursor()
            # TODO check min balance
            query = "update Account set acc_balance = acc_balance - ? where acc_no =?"
            cursor.execute(query, (amount, account_no))
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error in debit opertion: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def credit(self, account_no, amount):
        try:
            cursor = self.conn.cursor()
            query = "update Account set acc_balance = acc_balance + ? where acc_no =?"
            cursor.execute(query, (amount, account_no))
            print(f"inserted {amount} into {account_no}")
            self.conn.commit()
        except mariadb.Error as e:
            print(f"Error in credit opertion: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def get_accounts(self, cust_id):
        try:
            cursor = self.conn.cursor()
            query = "select acc_no from Account where cust_id = ?"
            cursor.execute(query, (cust_id,))
            return cursor.fetchall()
        except mariadb.Error as e:
            print(f"Error getting account numbers: {e}")
        finally:
            cursor.close()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
