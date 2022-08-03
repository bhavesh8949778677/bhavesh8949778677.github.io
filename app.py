import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


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
    """Show portfolio of stocks"""
    data = db.execute("SELECT symbol,SUM(shares) as shares,price, stock_name from 'transaction' WHERE user_id==? GROUP BY symbol ", session.get("user_id"))
    cash1 = db.execute("SELECT cash FROM users WHERE id==?", session.get("user_id"))
    cash = cash1[0]['cash']
    total = cash
    for x in data:
        total += x["shares"]*x["price"]
    return render_template("index.html", data = data, cash = cash, total = total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method=="GET":
        return render_template("buy.html")

    if request.method=="POST":
        if not request.form.get("symbol"):
            return apology("Missing Symbol",403)
        if not request.form.get("shares"):
            return apology("Missing number of shares",403)
        symbol=request.form.get("symbol")
        shares=request.form.get("shares")
        if lookup(symbol.upper()) is not None:
            # try:
            #     shares=int(shares)
            # except:
            if (shares.isdigit()==False):
                return apology("Number of Shares must be a positive integer")
            shares=int(shares)
            if shares > 0 :
                ans=lookup(symbol)
                cost=shares*ans["price"]

                user_id=session.get("user_id")
                cash1=db.execute("SELECT cash FROM users WHERE id==?", session.get("user_id"))

                cash=cash1[0]['cash']
                if cash<cost:
                    return apology("Cannot afford")
                new_cash = cash - cost
                db.execute("UPDATE users SET cash=? WHERE id==?", new_cash , session.get("user_id"))

                date = datetime.datetime.now()
                db.execute("INSERT INTO 'transaction' (user_id, symbol, shares, price, date, stock_name) VALUES (?,?,?,?,?,?)", session.get("user_id"), symbol, shares, ans["price"], date, lookup(symbol.upper())["name"])
                flash("Bought!")
                return index()
                # if cash[0]['cash']>cost:
                #     cash[0]['cash']-=cost
                #     print(cash[0]['cash'])
                #     return render_template("index.html")
                # else:
                #     return apology("Cannot afford!")
            else:
                return apology("Number of shares must be a positive integer")
        else:
            return apology("INVALID SYMBOL")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    if request.method=="GET":
        data=db.execute("SELECT symbol,shares,price,date FROM 'transaction' WHERE user_id==?", session.get("user_id"))
        return render_template("history.html",data=data)

    return apology("TODO")


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method=="GET":
        return render_template("quote.html")
    if request.method=="POST":
        if not request.form.get("symbol"):
            return apology("Missing Symbol")
        symbol=request.form.get("symbol")
        if lookup(symbol.upper()) is not None:
            answer=lookup(symbol.upper())
            return render_template("quoted.html",answer=answer)
        else:
            return apology("INVALID SYMBOL")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method=="GET":
        return render_template("register.html")
    if request.method=="POST":
            # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("confirmation"):
            return apology("must cofirm password",400)
        elif request.form.get("password")!=request.form.get("confirmation"):
            return apology("enter same password as before",400)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if (len(rows)!=0):
            return apology("Username is taken",400)
        else:
            db.execute("INSERT INTO users (username,hash) VALUES (?,?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
            return login()


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method=="GET":
        symbols=db.execute("SELECT symbol,SUM(shares) AS shares from 'transaction' WHERE user_id==? GROUP BY symbol", session.get("user_id"))
        return render_template("sell.html",symbols=symbols)


    if request.method=="POST":
        # if valid
        if not request.form.get("symbol"):
            return apology("Missing Symbol",403)
        if not request.form.get("shares"):
            return apology("Missing number of shares",403)
        symbol=request.form.get("symbol")
        shares=request.form.get("shares")
        if lookup(symbol.upper()) is not None:
            try:
                shares=int(shares)
            except:
                return apology("Number of Shares must be a positive integer")
            if shares > 0 :
                ans=lookup(symbol)
                cost=shares*ans["price"]

                user_id=session.get("user_id")
                cash1=db.execute("SELECT cash FROM users WHERE id==?", session.get("user_id"))
                share1=db.execute("SELECT SUM(shares) AS shares FROM 'transaction' WHERE user_id==? AND symbol==?", session.get("user_id"), symbol)
                cash=cash1[0]['cash']
                if share1[0]['shares']<shares:
                    return apology("Too Many Shares")
                new_cash = cash + cost
                db.execute("UPDATE users SET cash=? WHERE id==?", new_cash , session.get("user_id"))

                date = datetime.datetime.now()
                db.execute("INSERT INTO 'transaction' (user_id, symbol, shares, price, date, stock_name) VALUES (?,?,?,?,?,?)", session.get("user_id"), symbol, (-1)*shares, ans["price"], date, lookup(symbol.upper())["name"])
                flash("Sold!")
                return index()
                # if cash[0]['cash']>cost:
                #     cash[0]['cash']-=cost
                #     print(cash[0]['cash'])
                #     return render_template("index.html")
                # else:
                #     return apology("Cannot afford!")
            else:
                return apology("Number of shares must be a positive integer")
        else:
            return apology("INVALID SYMBOL")
    return apology("TODO")


@app.route("/cp", methods=["GET", "POST"])
@login_required
def cp():
    if request.method =="GET":
        return render_template("cp.html")
    if request.method == "POST":
        # Ensure old was submitted
        if not request.form.get("oldpassword"):
            return apology("must provide previous password", 403)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)
        if not request.form.get("confirmation"):
            return apology("must cofirmm the new password", 403)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("confirm password and password should be same", 403)
        oldpassword = request.form.get("oldpassword")
        newpassword = request.form.get("password")

        rows = db.execute("SELECT * FROM users WHERE id == ?", session.get("user_id"))

        # Ensure username exists and password is correct
        if not check_password_hash(rows[0]["hash"], oldpassword):
            return apology("invalid old password", 403)

        # Remember which user has logged in
        if oldpassword == newpassword:
            return apology("New password is same as old passwrd")

        db.execute("UPDATE users SET hash=? WHERE id==?", generate_password_hash(newpassword), session.get('user_id'))

        flash("Your Password Is Changed Successfully")
        return redirect("/")
