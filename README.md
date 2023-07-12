# FINANCE
Stock Trading App that logs stock performance in a user's portfolio.

## Description
Finance is a web application that enables a user to buy and sell shares. It provides an up-to-date analysis of the user's portfolio depending on current market price. Stock prices are queried from Yahoo Finance API. The project contains the following:
- app.py - This is a python file that initializes a Flask application and renders different HTML templates depending on what the user requests. It contains code that validates user login credentials, registers a new user, logs out the user, and coordinates buying and selling of shares.
- finance.db - SQLite database that stores user credentials and transaction information for every user.
- finance.sql - Contains SQL queries used to create and alter tables.
- helpers.py - Python file containing code used to query Yahoo Finance API, provide a login required decorator, and render error messages displayed to the user.
- requirements.txt - Contains installations required to run the application.
- static
    - styles.css - Contains styling code for the different HTML templates.
- templates - Folder containing the different HTML pages rendered to the user.

## Getting Started
Finance is a web application that is accessed through its URL.


