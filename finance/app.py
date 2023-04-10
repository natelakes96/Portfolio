import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

#api public key : pk_1c43fdaea034419781382de9ede2b039

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


    #getting users holdings and cash position
    userid = session["user_id"]
    info = db.execute("SELECT cash, username FROM users WHERE id = ?", userid)
    username = info[0]["username"]
    cash = float(info[0]["cash"])
    holdings = db.execute("SELECT * FROM Portfolios WHERE user_id= ? GROUP BY symbol", userid)

    #this updates the holdings to have the current prices of the stock
    tickers = []
    g=0
    for x in holdings:
        tickers.append(holdings[g]["symbol"])
        g += 1

    if tickers == None:
        return apology("Buy some stocks to see your portfolio!")

    for x in tickers:
        newprice= lookup(x)
        newprice = newprice["price"]
        db.execute("UPDATE Portfolios SET price = ? WHERE symbol = ?", newprice, x)
    holdings = db.execute("SELECT * FROM Portfolios WHERE user_id= ? GROUP BY symbol", userid)

    #sums all holdings
    total_holdings= db.execute("SELECT SUM(price) AS price FROM Portfolios WHERE user_id = ?", userid)
    total_holdings = total_holdings[0]["price"]
    if total_holdings == None:
        total_holdings = 0
    total_holdings_cash = total_holdings + cash

    #renders html template
    return render_template("index.html", holdings=holdings, username=username, cash=cash, total_holdings=total_holdings, total_holdings_cash=total_holdings_cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":

        #get together data for buy functions
        ticker = request.form.get("symbol")
        ticker = ticker.upper()
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("Cant buy that amount of shares!")
        if shares < 0:
            return apology("Cant buy that amount of shares!")

        #looks up ticker and assigns data values and checks if ticker exists
        info = lookup(ticker)
        if info == None:
            return apology("That isnt a valid ticker symbol! :(")

        price = float(info["price"])

        #finds amount of money the user has
        userid = session["user_id"]
        user_money = db.execute("SELECT cash FROM users WHERE id IS ?", userid)
        user_cash = user_money[0]["cash"]


        #determins if user has enough money
        if (price * shares) > user_cash:
            return apology("You cant afford that many shares! :(")

        #changes the amount of money in users account
        new_cash = user_cash - (price * shares)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, userid)

        #add a transaction
        date = datetime.datetime.now()
        db.execute("INSERT INTO Transactions (user_id, symbol, price, shares, date) VALUES (?, ?, ?, ?, ?)", userid, ticker, price, shares, date)


        #add stock to portfolio

        #gets list of stocks already owned
        holdings = db.execute("SELECT * FROM Portfolios WHERE user_id= ? GROUP BY symbol", userid)
        tickers = []
        g=0
        for x in holdings:
            tickers.append(holdings[g]["symbol"])
            g += 1



        if ticker in tickers:
            user_shares = db.execute("SELECT shares FROM portfolios WHERE user_id = ? AND symbol = ?", userid, ticker)
            user_shares = user_shares[0]["shares"]
            db.execute("UPDATE portfolios SET shares = ? WHERE user_id = ? AND symbol = ?", (shares + user_shares) ,userid, ticker)

        db.execute("INSERT INTO Portfolios (user_id, symbol, price, shares) VALUES (?, ?, ?, ?)", userid, ticker, price, shares)

        #say that user bought the stock
        flash("Purchase Sucessful!")

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    #getting transactions
    userid = session["user_id"]
    transactions = db.execute("SELECT symbol, price, shares, date FROM transactions WHERE user_id = ?", userid)


    return render_template("history.html", transactions=transactions)


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
    if request.method == "POST":

        #retreiving user input
        symbol = request.form.get("symbol")

        #making a variable that stores the symbol info
        info = lookup(symbol)

        #checking if ticker exists
        if info == None:
            return apology ("That isnt a valid ticker symbol! :(")

        name = info["name"]
        sym = info["symbol"]
        price = info["price"]


        #returns page with symbol info
        return render_template("quoted.html", name=name, symbol=sym, price=price)

    #get method to look at page
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        #initializing all data from form
        username = request.form.get("username")
        password = request.form.get("password")
        passwordCheck = request.form.get("confirmation")

        #checks for empty fields
        if username == '' or password == '' or passwordCheck == '':
            return apology("Must put a username and password!")

        #checks if username is inputed and if username is unique
        users = db.execute("SELECT username FROM users WHERE username IS ? ", username)

        if users != []:
            return apology("That username is already in use! :(")


        #check if password matches confirmation
        if password != passwordCheck:

            return apology("password and confirmation doesn't match! :(")

        #making a hash of a users password
        hash = generate_password_hash(password)

        #create a new user is finance.db
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

        #redirecting to login
        return redirect("/login")

    else:
        return render_template("register.html")







@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        #get the ticker they want to sell and shares
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        #gets amount of shares from the db
        userid = session["user_id"]
        info = db.execute("SELECT shares FROM Portfolios WHERE user_id = ? AND symbol = ?", userid, symbol)
        user_shares = int(info[0]["shares"])

        #checks if user has enough shares to sell
        if shares > user_shares or shares < 0:
            return apology("You cant sell that many shares! :(")

        #changes users amount of shares in portfolio and makes a transaction
        date = datetime.datetime.now()
        price = lookup(symbol)
        price= float(price["price"])
        new_shares = user_shares - shares
        db.execute("INSERT INTO Transactions (user_id, symbol, price, shares, date) VALUES (?, ?, ?, ?, ?)", userid, symbol, price, (shares * -1), date)
        db.execute("UPDATE Portfolios SET shares = ? WHERE user_id = ? AND symbol = ?", new_shares, userid, symbol)

        #add cash value back to users cash
        cash = db.execute("SELECT cash FROM users WHERE id = ?", userid )
        user_cash = float(cash[0]["cash"])
        stock_value = lookup(symbol)
        stock_value = float(stock_value["price"])
        new_cash = user_cash + (stock_value * shares)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, userid)



        #confirm sale
        flash( "Sale Sucessful!" )


        return redirect("/")



    if request.method == "GET":
        #gets list of stocks owned by user
        userid = session["user_id"]
        holdings = db.execute("SELECT * FROM Portfolios WHERE user_id= ? GROUP BY symbol", userid)
        tickers = []
        g=0
        for x in holdings:
            tickers.append(holdings[g]["symbol"])
            g += 1



        return render_template("sell.html", holdings=tickers)
