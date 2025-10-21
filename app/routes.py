from flask import Blueprint, flash, jsonify, redirect, render_template, request, session

from db.database import Database

main = Blueprint("main", __name__)

db_info = {"user": "root", "port": "3306", "host": "localhost", "database": "bank_db"}
db = Database(db_info)


@main.route("/")
def home():
    return render_template("login.html")


@main.route("/login", methods=["POST"])
def login():
    user_name = request.form.get("username", "").strip()
    # TODK passwlrd
    # password = request.form.get("password", "").strip()

    # if not user_name or not password:
    if not user_name:
        flash("Username and password are required.", "error")
        return redirect("/")  # Redirect back to the login page

    # print(f"username: {user_name}, password: {password}")

    select_query = "SELECT * FROM Users WHERE Name = ?"
    user = db.execute_query(select_query, (user_name,))

    if user:
        print("Valid user")
        # Optionally, store user information in the session for later use
        session["user_id"] = user[0]  # Assuming user ID is the first element
        return redirect("/user")

    print("Invalid login attempt")
    flash("Invalid Username or password", "error")
    return redirect("/")


@main.route("/user")
def user_page():
    user_id = session.get("user_id")
    if not user_id:
        flash("You need to log in first.", "error")
        return redirect("/")  # Redirect to the login page if not authenticated

    # Fetch user information from the database
    user = db.retrieve_user_info()
    if user:
        userinfo = {
            "user_name": user[0],
            "email": user[1],
            "start_date": user[2],
            "account_type": user[3],
            "account_balance": user[4],
        }

    if not user:
        flash("User not found.", "error")
        return redirect("/")

    return render_template("user_page.html", user=userinfo)


@main.route("/debit", methods=["GET"])
def get_debit():
    user_id = session["user_id"]
    if not user_id:
        redirect("/")
    accounts = db.get_accounts(user_id)
    acc_nums = [acc[0] for acc in accounts]
    return render_template("debit.html", accounts=acc_nums)


@main.route("/debit", methods=["POST"])
def post_debit():
    account_no = request.json.get("account_no")
    amount = request.json.get("amount")

    print(account_no, amount)

    if not account_no or not amount:
        return jsonify({"error": "Missing account number or amount"}), 400

    if not db.check_account_exist(account_no):
        return jsonify({"error": "Account_no does not exist"}), 400

    db.debit(account_no, amount)
    response_message = f"Successfully debit {amount} from {account_no}."
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
    user_id = session.get("user_id")
    if not user_id:
        flash("You need to log in first.", "error")
        return redirect("/")  # Redirect to the login page if not authenticated

    transactions = db.getTransactions(user_id)
    return render_template("transaction.html", transactions=transactions)


@main.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/")
