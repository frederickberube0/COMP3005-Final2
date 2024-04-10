import psycopg2
from getpass import getpass
from psycopg2 import sql
from admins.admin_functions import get_hash, safe_int_input, is_valid_email, is_unique_email
from members.members_functions import update_member_info, update_fitness_goals, display_member_info

#This file is no longer being used since we transfered from being a CLI to a Flask App

DEBUG = False

def main():
    # Database connection parameters
    userid = -1
    role = ""
    dbname = ""
    user = ""
    dbpassword = ""
    host = ""
    port = ""

    if DEBUG:
        dbname = input("database name (default=ProjectV2): ")
        user = input("user name (default=postgres): ")
        dbpassword = input("password (default=postgres): ")
        host = input("host (default=localhost): ")
        port = input("port (default=5432): ")

    if dbname == "": dbname = "ProjectV2"
    if user == "": user = "postgres"
    if dbpassword == "": dbpassword = "postgres"
    if host == "": host = "localhost"
    if port == "": port = "5432"

    #Attempt database connection
    try: 
        conn = psycopg2.connect(dbname=dbname, user=user, password=dbpassword, host=host, port=port)
        cursor = conn.cursor()
    except psycopg2.Error as e:
        print(f"Error running sql command: {e}")
        exit()

    choice = -1
    print("""Would you like to
    1. Register
    2. Login""")

    while choice == -1:
        choice = safe_int_input(input("Enter your choice: "))
    
    if choice == 1:
        (userid, role) = register(conn)
    else:
        (userid, role) = login(conn)

    if role == "Member": memberPath(conn, userid)
    elif role == "Admin": adminPath(conn, userid)
    elif role == "Trainer": trainerPath(conn, userid)
    else: print("ERROR. Invalid role detected.")

    conn.commit()
    cursor.close()
    conn.close()

def login(conn) -> tuple[int, str]:
    """Logins a user and returns their userID and role."""
    while True:
        email = input("Enter your email: ")
        if not is_valid_email(conn, email): 
            continue

        password_hash = get_hash(getpass("Enter your password: "))
        
        query = "SELECT id, role FROM Users WHERE email = %s AND password = %s"
        
        with conn.cursor() as cur:
            cur.execute(query, (email, password_hash))
            result = cur.fetchone()
            
            if result:
                print("Login successful.", result)
                return result 
            else:
                print("Login failed. Check your email and password and try again.")

def register(conn) -> tuple[int, str]:
    """Registers and returns the current (userid, role)"""
    pMatch = False
    emailValid = False
    while not emailValid:
        email = input("Enter an email: ") #check for duplicate
        emailValid = is_valid_email(conn, email) and is_unique_email(conn, email)

    while not pMatch:
        password = get_hash(getpass("Enter a password: "))
        vPassword = get_hash(getpass("Verify your password: "))
        pMatch = password == vPassword
        if not pMatch: print("Passwords did not match.")
    cur = conn.cursor()
    role = "Member"
    cur.execute("INSERT INTO Users (email, password, role) VALUES (%s, %s, %s) RETURNING id", (email, password, role))
    userid = cur.fetchone()[0]
    print("Thanks, now we will make you fill out a member signup survey")

    name = ""
    memberHeight = -1
    memberEnduranceScale = -1
    memberWeight = -1
    memberWeight = -1
    memberStengthScale = -1
    age = -1
    gender = ""

    while name == "" and len(name) < 255:
        name = input("What is your name: ")
    while age < 0 or age > 99:
        age = safe_int_input(input("What is your current age?: "))
    while gender != "Male" and gender != "Female":
        gender = input("What is your gender? (Male/Female): ")
    while memberHeight < 0 or memberHeight > 250:
        memberHeight = safe_int_input(input("What is your current height? (cm): "))
    while memberWeight < 0 or memberWeight > 999:
        memberWeight = safe_int_input(input("What is your current weight? (lb): "))
    while memberWeight < 0 or memberWeight > 999:
        memberWeight = safe_int_input(input("What is your desired weight? (lb): "))
    while memberEnduranceScale == -1:
        memberEnduranceScale = safe_int_input(input("On a scale of 1-5, how important is cardio for you: "))
    while memberStengthScale == -1:
        memberStengthScale = safe_int_input(input("On a scale of 1-5, how important is strength for you: "))

    cur.execute("INSERT INTO Members (id, name, age, gender) VALUES (%s, %s, %s, %s)", (userid, name, age, gender))
    cur.execute("""INSERT INTO Health_Metrics (member_id, height, weight, desired_weight, endurance_importance, strength_importance)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (userid, memberHeight, memberWeight, memberWeight, memberEnduranceScale, memberStengthScale))
    
    return (userid, role)

def memberPath(conn, userid):
    print("""
What would you like to do?
    1. Update member information
    2. Update fitness goals
    3. Schedule a training session""")
    choice = -1

    while choice == -1:
        choice = safe_int_input(input("Enter your choice: "))
    
    if choice == 1: update_member_info(conn, userid)
    elif choice == 2: update_fitness_goals(conn, userid)


    # display_member_info(conn, userid)
    # update_member_info(conn, userid)
    #update_fitness_goals(conn, userid)
    
def adminPath(conn, userid):
    print("""
What would you like to do?
    1. Create a trainer
    2. Create an admin
    3. Create a class
    4. Create a room""")

def trainerPath(conn, userid):
    print("""
What would you like to do?
    1. Change availiblities
    2. See upcoming classes""")

if __name__ == "__main__":
    main()