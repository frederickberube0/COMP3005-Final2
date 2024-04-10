import hashlib
import re

def safe_int_input(inputString):
    try:
        return int(inputString)
    except TypeError:
        print("Invalid input provided.")
        return -1
    
def get_hash(inputString):
    """Takes a string and returns it's sha256 hash"""
    encoded_string = inputString.encode()
    sha256_hash = hashlib.sha256()
    sha256_hash.update(encoded_string)
    hex = sha256_hash.hexdigest()

    return hex

def is_valid_email(conn, email) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        print("Invalid email format. Please try again.")
        return False 
    return True

def is_unique_email(conn, email) -> bool:
    with conn.cursor() as cur:
        query = "SELECT email FROM Users WHERE email = %s"
        cur.execute(query, (email,))
        
        if cur.fetchone():
            print("Email is already in use. Please try again.")
            return False
    return True

