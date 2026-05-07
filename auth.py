import bcrypt
from database import get_user_by_email, create_user, create_account

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def signup_user(full_name, email, password):
    if get_user_by_email(email):
        return False, "Email already registered!"
    hashed = hash_password(password)
    user_id = create_user(full_name, email, hashed)
    # Default savings account banao
    acc_no = create_account(user_id, 'Savings')
    return True, f"Account created! Account No: {acc_no}"

def login_user(email, password):
    user = get_user_by_email(email)
    if not user:
        return False, None, "Email not found!"
    if not verify_password(password, user['password_hash']):
        return False, None, "Wrong password!"
    return True, user, "Login successful!"