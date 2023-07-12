import os
import datetime
import pytz

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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
    db.execute('DELETE FROM summary')
    id = session.get('user_id')
    details = db.execute("SELECT symbol, SUM(shares_bought) AS bought, SUM(shares_sold) AS sold, cash FROM transactions JOIN users ON users.id = transactions.person_id WHERE person_id = ? GROUP BY symbol ORDER BY symbol", id)
    cash = 0
    for row in details:
        symbol = row['symbol']
        bought = row['bought']
        sold = row['sold']
        shares = bought - sold
        cash = row['cash']
        look = lookup(symbol)
        price = look['price']
        totals = price * shares
        db.execute('INSERT INTO summary(id, symbol, shares, current, totals, cash) VALUES (?, ?, ?, ?, ?, ?)', id, symbol, shares, price, totals, cash)

    portfolio = db.execute('SELECT * FROM summary')

    return render_template('index.html', portfolio=portfolio, cash=cash)

@app.route('/password', methods=['GET', 'POST'])
def change():
#change password function
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        newpass = request.form.get('newpass')
        confirmation = request.form.get('confirmation')

        #check user credentials, and allow them to change password
        if not password or not username or not newpass or not confirmation:
            return apology('Please fill out all fields')
        if newpass != confirmation:
            return apology('New passwords do not match')

        user = db.execute('SELECT * FROM users WHERE username = ?', username)
        #check if user exists
        if len(user)!= 1 or not check_password_hash(user[0]['hash'], password):
            return apology("Incorrect username or password")
        else:
            new = generate_password_hash(newpass, method='pbkdf2:sha256', salt_length=8)
            db.execute('UPDATE users SET hash = ? WHERE username = ?', new, username)
        #clear user session to log in again
        session.clear()
        return redirect('/login')

    return render_template('change.html')

@app.route('/quickbuy', methods=['GET', 'POST'])
@login_required
def quickbuy():
    #Quickly buy shares
    if request.method == 'POST':
        symbol = request.form.get('symbol', 0)
        amount = request.form.get('shares')
        details = lookup(symbol)
        if not amount.isdecimal():
            return apology("Enter valid amount")
        amount = int(amount)
        if amount < 0:
            return apology("Enter valid amount")
        price = details['price']
        spend = price * amount
        id = session.get('user_id')
        existing = db.execute('SELECT cash FROM users WHERE id = ?', id)
        for amts in existing:
            if spend > amts['cash']:
                return apology('You do not have sufficient funds to complete transaction')
        remaining = amts['cash'] - spend
        db.execute("UPDATE users SET cash = ? WHERE id = ?", remaining, id)
        current_time = datetime.datetime.now(pytz.timezone("US/Eastern"))
        symbol = symbol.lower()
        db.execute('INSERT INTO transactions(person_id, symbol, share_price, shares_bought, amount_spent, transaction_time) VALUES (?, ?, ?, ?, ?, ?)', id, symbol, price, amount, spend, current_time)
        return redirect('/')

    return render_template('quickbuy.html')


@app.route('/quicksell', methods=['GET', 'POST'])
@login_required
def quicksell():
    #Quickly sell shares
    if request.method == 'POST':
        id = session.get('user_id')
        symbol = request.form.get('symbol', 0)
        symbol = symbol.lower()
        portfolio = db.execute('SELECT symbol, shares, cash FROM summary WHERE id = ?', id)
        amount = request.form.get('shares')
        if not amount.isdecimal():
            return apology("Enter valid amount")
        amount = int(amount)
        if amount < 0:
            return apology("Enter valid amount")
        for stocks in portfolio:
            if symbol in stocks.values():
                if amount > stocks['shares']:
                    return apology("You do not own that many shares")
                else:
                    details = lookup(symbol)
                    price = details['price']
                    gain = price * amount
                    cash = stocks['cash']
                    total = cash + gain
                    current_time = datetime.datetime.now(pytz.timezone("US/Eastern"))
                    db.execute('INSERT INTO transactions(person_id, symbol, share_price, shares_sold, amount_gained, transaction_time) VALUES(?,?,?,?,?,?)', id, symbol, price, amount, gain, current_time)
                    db.execute('UPDATE users SET cash = ? WHERE id = ?', total, id)
                    return redirect('/')
            else:
                continue
    return render_template('quicksell.html')


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    if request.method == 'POST':
        id = session.get('user_id')
        amount = request.form.get('amt')
        if not amount.isdecimal():
            return apology("Enter valid amount")
        amount = int(amount)
        if amount < 0:
            return apology("Enter valid amount")
        current = db.execute('SELECT cash FROM users WHERE id = ?', id)
        new = amount + current[0]['cash']
        db.execute('UPDATE users SET cash = ? WHERE id = ?', new, id)
        return redirect('/')

    return render_template('update.html')

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        details = lookup(symbol)
        if not symbol or not details:
            return apology("Enter valid stock symbol")
        amount = request.form.get('shares')
        if not amount.isdecimal():
            return apology("Enter valid amount")
        amount = int(amount)
        if amount < 0:
            return apology("Enter valid amount")
        price = details['price']
        spend = price * amount
        id = session.get('user_id')
        existing = db.execute('SELECT cash FROM users WHERE id = ?', id)
        for amts in existing:
            if spend > amts['cash']:
                return apology('You do not have sufficient funds to complete transaction')
        remaining = amts['cash'] - spend
        db.execute("UPDATE users SET cash = ? WHERE id = ?", remaining, id)
        current_time = datetime.datetime.now(pytz.timezone("US/Eastern"))
        symbol = symbol.lower()
        db.execute('INSERT INTO transactions(person_id, symbol, share_price, shares_bought, amount_spent, transaction_time) VALUES (?, ?, ?, ?, ?, ?)', id, symbol, price, amount, spend, current_time)
        return redirect('/')

    return render_template('buy.html')


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    id = session.get('user_id')
    past = db.execute("SELECT symbol, share_price, shares_bought, shares_sold, transaction_time FROM transactions WHERE person_id = ?", id)
    return render_template("history.html", past=past)


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
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        details = lookup(symbol)
        if details:
            return render_template('quoted.html', details=details)
        else:
            return apology("Stock not found")
    return render_template('quote.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        usernames = db.execute("SELECT username FROM users")
        if not username:
            return apology("Please enter a username")
        for users in usernames:
            if username in users.values():
                return apology("Username already exists")
        if password != confirmation:
            return apology('Passwords do not match')
        elif not password or not confirmation:
            return apology('Please enter password')

        hashedpass = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db.execute('INSERT INTO users(username, hash) VALUES (?, ?)', username, hashedpass)
        return redirect('/login')
    return render_template('register.html')


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    id = session.get('user_id')
    all = db.execute('SELECT symbol FROM summary WHERE id = ?', id)
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        symbol = symbol.lower()
        portfolio = db.execute('SELECT symbol, shares, cash FROM summary WHERE id = ?', id)
        if not symbol:
            return apology("Please select a stock")
        count = 0
        for stocks in portfolio:
            if symbol == stocks['symbol']:
                count += 1
                break
        if count == 0:
            return apology("You do not own selected stock")
        amount = request.form.get('shares')
        if not amount.isdecimal():
            return apology("Enter valid amount")
        amount = int(amount)
        if amount < 0:
            return apology("Enter valid amount")
        for stocks in portfolio:
            if symbol in stocks.values():
                if amount > stocks['shares']:
                    return apology("You do not own that many shares")
                else:
                    details = lookup(symbol)
                    price = details['price']
                    gain = price * amount
                    cash = stocks['cash']
                    total = cash + gain
                    current_time = datetime.datetime.now(pytz.timezone("US/Eastern"))
                    db.execute('INSERT INTO transactions(person_id, symbol, share_price, shares_sold, amount_gained, transaction_time) VALUES(?,?,?,?,?,?)', id, symbol, price, amount, gain, current_time)
                    db.execute('UPDATE users SET cash = ? WHERE id = ?', total, id)
                    return redirect('/')
            else:
                continue

    return render_template('sell.html', stocks=all)
