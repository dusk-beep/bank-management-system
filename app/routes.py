from flask import Blueprint, flash, jsonify, redirect, render_template, request, session

from db.database import Database

main = Blueprint("main", __name__)

db_info = {"user": "root", "port": "3306", "host": "localhost", "database": "bankDb"}
db = Database(db_info)


@main.route("/")
def home():
    return render_template("login.html")


@main.route("/login", methods=["POST"])
def login():
    user_name = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role")

    if not user_name or not password:
        flash("Username and password are required.", "error")
        return redirect("/")  # Redirect back to the login page

    if role == "employee":
        select_query = "SELECT * FROM Employee WHERE emp_name = ? and password = ?"
        emp = db.execute_query(select_query, (user_name, password))
        if emp:
            session["emp_id"] = emp[0]  # Assuming user ID is the first element
            return redirect("/employee")
        else:
            print("Invalid login attempt")
            flash("Invalid Username or password", "error")
            return redirect("/")

    elif role == "customer":
        select_query = "SELECT * FROM Customer WHERE cust_name = ? and password = ?"
        user = db.execute_query(select_query, (user_name, password))
        if user:
            session["cust_id"] = user[0]  # Assuming user ID is the first element
            return redirect("/user")
        else:
            print("Invalid login attempt")
            flash("Invalid Username or password", "error")
            return redirect("/")


@main.route("/employee")
def emp_dashboard():
    emp_id = session.get("emp_id")
    if not emp_id:
        flash("You need to log in first.", "error")
        return redirect("/")
    return render_template("emp_dashboard.html")


@main.route("/create_account", methods=["POST"])
def create_account():
    try:
        data = request.get_json()  # Use get_json for JSON request
        cust_name = data.get("cust_name", "").strip()
        cust_email = data.get("cust_email")
        password = data.get("password", "").strip()
        acc_type = data.get("acc_type")
        balance = float(data.get("balance", 0))  # Convert to float

        cust_id = int(db.insert_users(cust_name, cust_email, password)[0])
        db.insert_accounts(cust_id, acc_type, balance)

        return jsonify({"message": "Successfully created account"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400  # Return error message


@main.route("/user")
def user_page():
    cust_id = session.get("cust_id")
    if not cust_id:
        flash("You need to log in first.", "error")
        return redirect("/")  # Redirect to the login page if not authenticated

    user = db.retrieve_user_info(cust_id)
    if user:
        userinfo = {
            "user_name": user[0][0],  # Cust name from the first account
            "email": user[0][1],  # Cust email from the first account
            "start_date": user[0][2],  # Start date from the first account
            "accounts": [],  # Initialize accounts list
        }

        for account in user:
            userinfo["accounts"].append(
                {"account_type": account[3], "account_balance": account[4]}
            )
    if not user:
        flash("User not found.", "error")
        return redirect("/")

    return render_template("user_dashboard.html", user=userinfo)


@main.route("/transfer", methods=["GET"])
def get_debit():
    cust_id = session["cust_id"]
    if not cust_id:
        redirect("/")
    accounts = db.get_accounts(cust_id)
    acc_nums = [acc[0] for acc in accounts]
    return render_template("transfer.html", accounts=acc_nums)


@main.route("/transfer", methods=["POST"])
def post_debit():
    from_acc_no = request.json.get("from_acc_no")
    to_acc_no = request.json.get("to_acc_no")
    amount = request.json.get("amount")

    if not from_acc_no or not amount or not to_acc_no:
        return jsonify({"error": "Missing account number or amount"}), 400

    if not db.check_account_exist(to_acc_no):
        return jsonify({"error": "Account_no does not exist"}), 400

    if not db.minimum(from_acc_no):
        return jsonify({"error": "Account does not have minimum balance"}), 400

    db.debit(from_acc_no, amount)
    db.credit(to_acc_no, amount)
    db.setTransactions(from_acc_no, to_acc_no, amount)
    response_message = f"Successfully transfered {amount} to {to_acc_no}."
    return jsonify({"message": response_message}), 200


@main.route("/credit", methods=["GET"])
def deposit():
    user_id = session["user_id"]
    if not user_id:
        redirect("/")
    accounts = db.get_accounts(user_id)
    acc_nums = [acc[0] for acc in accounts]
    return render_template("credit.html", accounts=acc_nums)


@main.route("/credit", methods=["POST"])
def deposite_check():
    account_no = request.json.get("account_no")
    amount = request.json.get("amount")

    print(account_no, amount)

    if not account_no or not amount:
        return jsonify({"error": "Missing account number or amount"}), 400

    if not db.check_account_exist(account_no):
        return jsonify({"error": "Account_no does not exist"}), 400

    db.credit(account_no, amount)
    response_message = f"Successfully deposited {amount} to account {account_no}."
    return jsonify({"message": response_message}), 200


@main.route("/transactions/")
def view_transactions():
    cust_id = session.get("cust_id")

    if not cust_id:
        flash("You need to log in first.", "error")
        return redirect("/")  # Redirect to the login page if not authenticated

    accounts = db.get_accounts(cust_id)
    acc_nums = [acc[0] for acc in accounts]

    transactions = []
    for acc in acc_nums:
        trans = db.getTransactions(acc)
        transactions.extend(trans)

    return render_template("transaction.html", transactions=transactions)


@main.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/")
