import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from webpush_handler import trigger_push_notifications_for_subscriptions
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import json

from helpers import apology, login_required

# Configure application
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('application.cfg.py')


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# use SQLite database
db = SQL("sqlite:///medicine.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show medicines"""

    rows = db.execute("SELECT name, schedule_time_1, schedule_time_2, schedule_time_3 FROM meds WHERE user_id = ?", session["user_id"])
    return render_template("index.html", medicines=rows)



@app.route("/add", methods=["GET", "POST"])
@login_required
def addMedicine():
    """Add Medicine"""

    if request.method == "GET":
        return render_template("add.html")
    else:
        name = request.form.get("name")
        if not name:
            return apology("Provide Name", 400)
        rows = db.execute("SELECT name FROM meds WHERE user_id = ? AND name = ?", session["user_id"], name)
        if (len(rows) != 0):
            return apology("This medicine is already added", 400)
        time1 = request.form.get("time1")
        if not time1:
            return apology("Provide Atleast one time", 400)
        time2 = request.form.get("time2")
        time3 = request.form.get("time3")


        rows = db.execute("INSERT INTO meds(user_id, name, schedule_time_1, schedule_time_2, schedule_time_3) VALUES (?,?,?,?,?)", session["user_id"], name, time1, time2, time3)

    return redirect("/")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def deleteMedicine():
    """Delete Medicine"""

    if request.method == "GET":
        rows = db.execute("SELECT name FROM meds where user_id = ?", session["user_id"])
        return render_template("delete.html", medicines=rows)
    else:
        name = request.form.get("name")
        rows = db.execute("DELETE FROM meds WHERE user_id = ? AND name = ?", session["user_id"], name)

    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
@login_required
def subscribe():
    """Show medicine alert"""
    json_data = request.get_json()
    subscription_json_string = json_data['subscription_json']
    subscription_json = json.loads(subscription_json_string)
    subscription_json.pop('expirationTime', None)
    subscription_json_string = json.dumps(subscription_json)
    rows = db.execute("SELECT id from subscriptions WHERE user_id = ? AND subscription_json = ?", session["user_id"],subscription_json_string)
    if (len(rows) == 0):
       rows = db.execute("INSERT INTO subscriptions(user_id, subscription_json) VALUES (?,?)", session["user_id"],subscription_json_string)
    return jsonify({
        "status": "success"
    })

@app.route("/alert", methods=["POST"])
def alert():
    """Alert"""

    title = "!!!! ALERT !!!!"
    rows = db.execute("SELECT user_id, name FROM meds WHERE schedule_time_1 BETWEEN TIME('now','localtime','-1 hour') AND TIME('now','localtime') OR schedule_time_2 BETWEEN TIME('now','localtime','-1 hour') AND TIME('now','localtime') OR schedule_time_3 BETWEEN TIME('now','localtime','-1 hour') AND TIME('now','localtime')")
    for row in rows:
        subRows = db.execute("SELECT * from subscriptions WHERE user_id = ? LIMIT 1", row["user_id"])
        print(len(subRows))
        if (len(subRows)) != 0:
            print("Going to send the web push")
            subscription = subRows[0]
            results = trigger_push_notifications_for_subscriptions(
                subscription,
                title,
                row["name"]
                )
        
    return jsonify("success")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("confirmation"):
            return apology("must provide confirm password", 400)
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password do not match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) == 1:
            return apology("username already exists", 400)

        hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username,hash) VALUES (?,?)", request.form.get("username"), hash)
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


