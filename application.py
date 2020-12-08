import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from MonteCarlo import monteCarloStockPrices, genCallPriceBuy, genSellOptionPrice
from math import log, exp
from statistics import mean, stdev, median
import random
from helpers import apology, login_required, lookup, usd

#
f = open('AAPL.csv','r')
f1 = open('CDNS.csv','r')
f2 = open('JNUG.csv','r')
f3 = open('DLTR.csv','r')
closing_stock_prices = [monteCarloStockPrices(f),monteCarloStockPrices(f1),monteCarloStockPrices(f2),monteCarloStockPrices(f3)]
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = db.execute("""
    SELECT symbol,price, SUM(shares) as totalShares

    FROM "transactions"

    WHERE user_id = :user_id

    GROUP BY symbol
    HAVING SUM(shares) >0
    """, user_id = session["user_id"])
    holdings = []
    grand_total = 0
    for row in rows:
        stock = lookup(row["symbol"])
        holdings.append({
            "symbol": row["symbol"],
            "shares": row["totalShares"],
            "price": row["price"],
            "total": usd(row["price"] * row["totalShares"])

        }
        )
        grand_total += row["price"] * row["totalShares"]
    rows2 = db.execute("SELECT cash FROM users WHERE id=:user_id", user_id = session["user_id"])
    cash = rows2[0]["cash"]
    grand_total +=cash

    return render_template("index.html", holdings=holdings, cash = usd(cash),grand_total = usd(grand_total))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        find_missing_errors = is_provided("symbol") or is_provided("shares")
        if find_missing_errors:
            return find_missing_errors
        elif not request.form.get("shares").isdigit():
            return apology("invalid number of shares", 403)
        symbol = request.form.get("symbol").upper()
        strike = int(request.form.get("strike"))
        shares = int(request.form.get("shares"))
        if symbol == "AAPL":
            option_chain = genCallPriceBuy(closing_stock_prices[0])
        elif symbol =="CDNS":
            option_chain = genCallPriceBuy(closing_stock_prices[1])
        elif symbol =="JNUG":
            option_chain = genCallPriceBuy(closing_stock_prices[2])
        elif symbol =="DLTR":
            option_chain = genCallPriceBuy(closing_stock_prices[3])
        #if stock is None:
        #    return apology("invalid symbol", 403)
        rows = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        cash = rows[0]["cash"]

        updated_cash = cash - shares * option_chain[strike]
        if updated_cash < 0:
            return apology("can't afford")
        db.execute("UPDATE users SET cash = :updated_cash WHERE id =:id",
            updated_cash = updated_cash,
            id = session["user_id"])
        # update transaction table

        db.execute("""
            INSERT INTO transactions (user_id, symbol, shares, price)
            VALUES (:user_id, :symbol, :shares, :price)
             """,
            user_id = session["user_id"],
            symbol = symbol + str(strike) + 'C',
            shares = shares,
            price = option_chain[strike])

        flash("Bought for " + usd(option_chain[strike]))


        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
   if request.method =="POST":
      db.execute("""UPDATE users
        SET cash = cash + :amount
        WHERE id = :user_id

      """, amount = request.form.get("cash"),
      user_id = session["user_id"])
      flash("Added Cash")
      return redirect("/")
   else:
       return render_template("add_cash.html")
@app.route("/getting_started")
@login_required
def getting_started():
    return render_template("getting_started.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("""
        SELECT symbol, shares, price,-1*shares*price as CashFlow, transacted
        FROM transactions
        WHERE user_id = :user_id
    """, user_id = session["user_id"])
    for i in range(len(transactions)):
        transactions[i]["price"] = usd(transactions[i]["price"])
        transactions[i]["CashFlow"] = usd(transactions[i]["CashFlow"])
    return render_template("history.html", transactions = transactions)

def is_provided(field):
     if not request.form.get(field):
            return apology(f"must provide {field}", 403)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username / password was submitted
        result_checks = is_provided("username") or is_provided("password")
        if result_checks is not None:
            return result_checks



        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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
    if request.method == "POST":
        result_check = is_provided("symbol")
        if result_check is not None:
            return result_check
        symbol = request.form.get("symbol").upper()
        strike = int(request.form.get("strike"))
        #stock = lookup(symbol)
        #if stock is None:
        #    return apology("invalid symbol", 400)
        if symbol == "AAPL":
            option_chain = genCallPriceBuy(closing_stock_prices[0])
        elif symbol =="CDNS":
            option_chain = genCallPriceBuy(closing_stock_prices[1])
        elif symbol =="JNUG":
            option_chain = genCallPriceBuy(closing_stock_prices[2])
        elif symbol =="DLTR":
            option_chain = genCallPriceBuy(closing_stock_prices[3])
        return render_template("quoted.html", symbol = symbol, strike = strike, optionPrice = usd(option_chain[strike]))
    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
   if request.method =="POST":
       result_checks = is_provided("username") or is_provided("password") or is_provided("confirmation")
       if result_checks != None:
           return result_checks
       if request.form.get("password") != request.form.get("confirmation"):
           return apology("passwords must match")
       try:
           prim_key = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                        username = request.form.get("username"),
                        hash = generate_password_hash(request.form.get("password")))
       except:
           return apology("username already exists", 403)
       if prim_key is None:
           return apology("registration error", 403)
       session["user_id"] =  prim_key
       return redirect("/")


   else:
        return render_template('register.html')


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        find_missing_errors = is_provided("symbol") or is_provided("shares")
        if find_missing_errors:
            return find_missing_errors
        elif not request.form.get("shares").isdigit():
            return apology("invalid number of shares", 403)
        symbol = request.form.get("symbol").upper()
        ticker = symbol[0:4]
        shares = int(request.form.get("shares"))
        strike = int(symbol[4:-1])
        if ticker == "AAPL":
            option_sell_chain = genSellOptionPrice(closing_stock_prices[0])
        elif ticker =="CDNS":
            option_sell_chain = genSellOptionPrice(closing_stock_prices[1])
        elif ticker =="JNUG":
            option_sell_chain = genSellOptionPrice(closing_stock_prices[2])
        elif ticker =="DLTR":
            option_sell_chain = genSellOptionPrice(closing_stock_prices[3])

        option_sell_price = option_sell_chain[strike]
        #if stock is None:
        #   return apology("invalid symbol", 403)

        rows = db.execute("""
            SELECT symbol, SUM(shares) as totalShares
            FROM transactions
            WHERE user_id = :user_id
            GROUP BY symbol
            HAVING totalShares > 0




        """, user_id = session["user_id"])
        for row in rows:
            if row["symbol"] == symbol:
                if shares > row["totalShares"]:
                    return apology("Cannot sell that many shares")

        rows = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        cash = rows[0]["cash"]

        updated_cash = cash + shares * option_sell_price


        db.execute("UPDATE users SET cash = :updated_cash WHERE id =:id",
            updated_cash = updated_cash,
            id = session["user_id"])
        # update transaction table

        db.execute("""
            INSERT INTO transactions (user_id, symbol, shares, price)
            VALUES (:user_id, :symbol, :shares, :price)
             """,
            user_id = session["user_id"],
            symbol = symbol,
            shares = -1 * shares,
            price = option_sell_price)

        flash("Sold for " + usd(option_sell_price) + '!')


        return redirect("/")
    else:
        rows = db.execute("""
            SELECT symbol
            FROM transactions
            WHERE user_id =:user_id
            GROUP BY symbol
            HAVING SUM(shares)>0
        """, user_id = session["user_id"])
        return render_template("sell.html", symbols = [row["symbol"]for row in rows])




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
