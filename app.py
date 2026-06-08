import streamlit as st
import pandas as pd
from auth import signup_user, login_user
from database import (
    get_user_accounts, create_account,
    get_account_by_number, transfer_money,
    get_mini_statement, add_transaction, update_balance,
    init_db
)

init_db()
st.set_page_config(
    page_title="SecureBank",
    page_icon="🏦",
    layout="centered"
)

st.markdown("""
<style>
.bank-header {
    text-align: center;
    padding: 1rem 0;
    border-bottom: 1px solid #eee;
    margin-bottom: 1.5rem;
}
.account-card {
    background: linear-gradient(135deg, #1a237e, #283593);
    color: white;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.balance-amount {
    font-size: 2rem;
    font-weight: bold;
}
.txn-credit { color: green; font-weight: 500; }
.txn-debit  { color: red;   font-weight: 500; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

# ── NOT LOGGED IN ──
if not st.session_state.logged_in:
    st.markdown('<div class="bank-header"><h2>🏦 SecureBank</h2><p>Your trusted digital bank</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Welcome back!")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary", use_container_width=True):
            if email and password:
                success, user, msg = login_user(email, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Please fill in all fields!")

    with tab2:
        st.subheader("Create Account")
        full_name = st.text_input("Full Name")
        email_s   = st.text_input("Email", key="signup_email")
        pass_s    = st.text_input("Password", type="password", key="signup_pass")
        pass_c    = st.text_input("Confirm Password", type="password")
        if st.button("Sign Up", type="primary", use_container_width=True):
            if full_name and email_s and pass_s and pass_c:
                if pass_s != pass_c:
                    st.error("Passwords do not match!")
                elif len(pass_s) < 6:
                    st.error("Password must be at least 6 characters!")
                else:
                    success, msg = signup_user(full_name, email_s, pass_s)
                    if success:
                        st.success(msg)
                        st.info("Please login now!")
                    else:
                        st.error(msg)
            else:
                st.warning("Please fill in all fields!")

# ── LOGGED IN ──
else:
    user = st.session_state.user
    accounts = get_user_accounts(user['id'])

    st.sidebar.markdown(f"### Hello, {user['full_name'].split()[0]}!")
    menu = st.sidebar.selectbox("Menu", [
        "🏠 Dashboard",
        "💸 Transfer Money",
        "📋 Mini Statement",
        "➕ Add Account",
        "💰 Deposit / Withdraw"
    ])
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    # ── DASHBOARD ──
    if menu == "🏠 Dashboard":
        st.title("🏠 Dashboard")
        total_balance = sum(a['balance'] for a in accounts)
        st.metric("Total Balance (All Accounts)", f"₹{total_balance:,.2f}")
        st.divider()

        st.subheader("Your Accounts")
        for acc in accounts:
            st.markdown(f"""
            <div class="account-card">
                <div style="font-size:13px;opacity:0.8">{acc['account_type']} Account</div>
                <div style="font-size:16px;letter-spacing:2px;margin:4px 0">{acc['account_number']}</div>
                <div class="balance-amount">₹{acc['balance']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TRANSFER ──
    elif menu == "💸 Transfer Money":
        st.title("💸 Transfer Money")
        acc_options = {
            f"{a['account_type']} — {a['account_number']} (₹{a['balance']:,.2f})": a['account_number']
            for a in accounts
        }

        from_key = st.selectbox("From Account", list(acc_options.keys()))
        to_acc   = st.text_input("To Account Number")
        amount   = st.number_input("Amount (₹)", min_value=1.0, value=100.0)
        desc     = st.text_input("Description (optional)", placeholder="Rent, Gift, etc.")

        if st.button("Transfer", type="primary", use_container_width=True):
            from_acc = acc_options[from_key]
            if not to_acc:
                st.warning("Please enter recipient account number!")
            elif to_acc == from_acc:
                st.warning("Cannot transfer to the same account!")
            elif not get_account_by_number(to_acc):
                st.error("Account number does not exist!")
            else:
                success, msg = transfer_money(from_acc, to_acc, amount, desc or "Transfer")
                if success:
                    st.success(f"✅ ₹{amount:,.2f} transferred successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

    # ── MINI STATEMENT ──
    elif menu == "📋 Mini Statement":
        st.title("📋 Mini Statement")
        acc_options = {
            f"{a['account_type']} — {a['account_number']}": a['account_number']
            for a in accounts
        }
        selected = st.selectbox("Select Account", list(acc_options.keys()))
        acc_no   = acc_options[selected]
        limit    = st.selectbox("Number of transactions", [5, 10, 20], index=1)

        txns = get_mini_statement(acc_no, limit)
        if txns:
            rows = []
            for t in txns:
                if t['to_account'] == acc_no:
                    txn_type   = "Credit"
                    amount_str = f"+₹{t['amount']:,.2f}"
                else:
                    txn_type   = "Debit"
                    amount_str = f"-₹{t['amount']:,.2f}"
                rows.append({
                    "Date":        str(t['transaction_date'])[:16],
                    "Type":        txn_type,
                    "Amount":      amount_str,
                    "Description": t['description'] or "-",
                    "From":        t['from_account'] or "-",
                    "To":          t['to_account'] or "-"
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No transactions found!")

    # ── ADD ACCOUNT ──
    elif menu == "➕ Add Account":
        st.title("➕ Open New Account")
        existing_types = [a['account_type'] for a in accounts]
        all_types      = ['Savings', 'Current', 'Salary']
        available      = [t for t in all_types if t not in existing_types]

        if not available:
            st.warning("You already have all three account types!")
        else:
            acc_type = st.selectbox("Account Type", available)
            st.info(f"A new {acc_type} account will be opened with ₹0 balance.")
            if st.button("Open Account", type="primary", use_container_width=True):
                acc_no = create_account(user['id'], acc_type)
                st.success(f"✅ {acc_type} Account opened successfully! Account No: {acc_no}")
                st.rerun()

    # ── DEPOSIT / WITHDRAW ──
    elif menu == "💰 Deposit / Withdraw":
        st.title("💰 Deposit / Withdraw")
        acc_options = {
            f"{a['account_type']} — {a['account_number']} (₹{a['balance']:,.2f})": a['account_number']
            for a in accounts
        }
        selected = st.selectbox("Select Account", list(acc_options.keys()))
        acc_no   = acc_options[selected]

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💵 Deposit", use_container_width=True):
                st.session_state['dw_mode'] = 'deposit'
        with col2:
            if st.button("💸 Withdraw", use_container_width=True):
                st.session_state['dw_mode'] = 'withdraw'

        mode = st.session_state.get('dw_mode', 'deposit')
        st.markdown(f"**Mode: {'Deposit' if mode == 'deposit' else 'Withdraw'}**")
        amount = st.number_input("Amount (₹)", min_value=1.0, value=1000.0)

        if st.button("Confirm", type="primary", use_container_width=True):
            if mode == 'deposit':
                update_balance(acc_no, amount)
                add_transaction(None, acc_no, amount, 'Credit', 'Cash Deposit')
                st.success(f"✅ ₹{amount:,.2f} deposited successfully!")
            else:
                acc = get_account_by_number(acc_no)
                if acc['balance'] < amount:
                    st.error("Insufficient balance!")
                else:
                    update_balance(acc_no, -amount)
                    add_transaction(acc_no, None, amount, 'Debit', 'Cash Withdrawal')
                    st.success(f"✅ ₹{amount:,.2f} withdrawn successfully!")
            st.rerun()
