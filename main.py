import os
import sys

import mariadb
from flask import Flask, flash, redirect, render_template, request

app = Flask(__name__)
app.secret_key = os.environ["FLASK_KEY"]
conn = None
cursor = None


def main():
    global conn, cursor
    try:
        conn = mariadb.connect(
            user="root", host="localhost", port=3306, database="mydb"
        )
        print("connected to mariadb")

        cursor = conn.cursor()

        try:
            cursor.execute("""
                   create table if not exists users (
                   id int auto_increment primary key,
                   username varchar(50) not null,
                   password varchar(50) not null
                );
                """)
            conn.commit()
        except mariadb.Error as e:
            print(f"Error creating table: {e}")
            conn.rollback()  # Rollback in case of DDL error
    except mariadb.Error as e:
        print("error connecting to mariadb: ", e)
        sys.exit(1)


main()


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/user")
def user():
    return "<p>user is successfully logged in</p>"


@app.route("/login", methods=["POST"])
def login():
    # insert_query = "insert into users (username,password) values (?,?)"
    select_query = "select * from users where username = ? and password = ?"
    username = request.form["username"].strip()
    password = request.form["password"].strip()
    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect("/")  # Redirect back to the login page

    print(f"username {username},password{password}")
    try:
        cursor.execute(select_query, (username, password))
        user = cursor.fetchone()
        print(user)

        if user:
            print("valid user")
            return redirect("/user")
        # cursor.execute(insert_query, (username, password))
        # conn.commit()
        # print("successfully inserted data")
    # except mariadb.IntegrityError as e:
    #     print(f"Error inserting data (might be duplicate email): {e}")
    #     conn.rollback()
    except mariadb.Error as e:
        print(f"Error inserting data: {e}")
        conn.rollback()

    print("invalid")
    flash("invalid Username or password", "error")
    return redirect("/")
