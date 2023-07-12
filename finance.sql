CREATE TABLE transactions(
    person_id INTEGER,
    symbol TEXT NOT NULL,
    share_price NUMERIC NOT NULL,
    shares_bought INTEGER NOT NULL,
    amount_spent NUMERIC NOT NULL,
    transaction_time TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES users(id)
);
CREATE TABLE sells(
    person_id INTEGER,
    symbol TEXT NOT NULL,
    share_price INTEGER NOT NULL,
    shares_sold INTEGER NOT NULL,
    amount_gained INTEGER NOT NULL,
    transaction_time TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES users(id)
);

SELECT symbol, SUM(shares_bought) AS shares, cash FROM transactions JOIN users ON users.id = transactions.person_id WHERE person_id = ? GROUP BY symbol ORDER BY symbol
CREATE TABLE summary(
    id INTEGER,
    symbol TEXT NOT NULL,
    shares INTEGER NOT NULL,
    current NUMERIC NOT NULL,
    totals NUMERIC NOT NULL,
    cash NUMERIC NOT NULL,
    FOREIGN KEY (id) REFERENCES users(id)
);


PRAGMA foreign_keys=off;

BEGIN TRANSACTION;
ALTER TABLE transactions RENAME TO transactions_old;

CREATE TABLE transactions(
    person_id INTEGER,
    symbol TEXT NOT NULL,
    share_price NUMERIC NOT NULL,
    shares_bought INTEGER NOT NULL DEFAULT 0,
    shares_sold INTEGER NOT NULL DEFAULT 0,
    amount_spent NUMERIC NOT NULL DEFAULT 0.00,
    amount_gained NUMERIC NOT NULL DEFAULT 0.00,
    transaction_time TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES users(id)
);
INSERT INTO transactions(person_id, symbol, share_price, shares_bought, amount_spent, transaction_time)
SELECT person_id, symbol, share_price, shares_bought, amount_spent, transaction_time
FROM transactions_old;

COMMIT;
PRAGMA foreign_keys=on;