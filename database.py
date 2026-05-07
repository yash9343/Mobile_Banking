import pymysql
import pymysql.cursors
from dotenv import load_dotenv
import os
import random
import string

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30,
        ssl_disabled=True
    )

def generate_account_number(account_type):
    prefix = {'Savings': 'SB', 'Current': 'CU', 'Salary': 'SA'}
    digits = ''.join(random.choices(string.digits, k=9))
    return prefix.get(account_type, 'SB') + digits

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(full_name, email, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (full_name, email, password_hash) VALUES (%s,%s,%s)",
        (full_name, email, password_hash)
    )
    conn.commit()
    user_id = conn.insert_id()
    conn.close()
    return user_id

def get_user_accounts(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM accounts WHERE user_id=%s ORDER BY created_at",
        (user_id,)
    )
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def create_account(user_id, account_type):
    conn = get_connection()
    cursor = conn.cursor()
    acc_no = generate_account_number(account_type)
    cursor.execute(
        "INSERT INTO accounts (user_id, account_number, account_type, balance) VALUES (%s,%s,%s,%s)",
        (user_id, acc_no, account_type, 0.00)
    )
    conn.commit()
    conn.close()
    return acc_no

def get_account_by_number(acc_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE account_number=%s", (acc_no,))
    acc = cursor.fetchone()
    conn.close()
    return acc

def update_balance(account_number, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accounts SET balance = balance + %s WHERE account_number=%s",
        (amount, account_number)
    )
    conn.commit()
    conn.close()

def add_transaction(from_acc, to_acc, amount, txn_type, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO transactions
        (from_account, to_account, amount, transaction_type, description)
        VALUES (%s,%s,%s,%s,%s)""",
        (from_acc, to_acc, amount, txn_type, description)
    )
    conn.commit()
    conn.close()

def get_mini_statement(account_number, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        WHERE from_account=%s OR to_account=%s
        ORDER BY transaction_date DESC
        LIMIT %s
    """, (account_number, account_number, limit))
    txns = cursor.fetchall()
    conn.close()
    return txns

def transfer_money(from_acc, to_acc, amount, description):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT balance FROM accounts WHERE account_number=%s", (from_acc,)
        )
        row = cursor.fetchone()
        balance = row['balance']
        if balance < amount:
            conn.close()
            return False, "Insufficient balance!"

        cursor.execute(
            "UPDATE accounts SET balance=balance-%s WHERE account_number=%s",
            (amount, from_acc)
        )
        cursor.execute(
            "UPDATE accounts SET balance=balance+%s WHERE account_number=%s",
            (amount, to_acc)
        )
        cursor.execute("""
            INSERT INTO transactions
            (from_account, to_account, amount, transaction_type, description)
            VALUES (%s,%s,%s,'Transfer',%s)
        """, (from_acc, to_acc, amount, description))

        conn.commit()
        conn.close()
        return True, "Transfer successful!"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)
