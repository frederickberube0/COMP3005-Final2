import psycopg2
from psycopg2 import sql

def update_member_info(conn, member_id):
    print("Select what you would like to update:")
    print("1. Name")
    print("2. Age")
    print("3. Gender")
    choice = input("Enter your choice: ")

    updates = []
    params = []
    #TODO: implement looping
    if choice == '1':
        name = input("Enter new name: ")
        updates.append("name = %s")
        params.append(name)
    elif choice == '2':
        age = input("Enter new age: ")
        if age.isdigit():
            updates.append("age = %s")
            params.append(age)
        else:
            print("Invalid input")
            return
    elif choice == '3':
        gender = input("Enter new gender: ")
        updates.append("gender = %s")
        params.append(gender)
    else:
        print("Invalid input")
        return

    execute_update(conn, "Members", updates, params, member_id)

def update_fitness_goals(conn, member_id):
    print("Select the fitness goal you would like to update:")
    print("1. Desired Weight Goal")
    print("2. Strength Importance")
    print("3. Endurance Importance")
    choice = input("Enter your choice (1-3)")

    updates = []
    params = []

    if choice == '1':
        desired_weight= input("Enter new desired weight: ")
        if desired_weight.isdigit():
            updates.append("desired_weight = %s")
            params.append(desired_weight)
    elif choice == '2':
        desired_strength = input("Enter new Strength Importance (1-5): ")
        if desired_strength.isdigit():
            updates.append("desired strength = %s")
            params.append(desired_strength)
    elif choice == '3':
        desired_endurance = input("Enter new EnduranceImportance (1-5): ")
        if desired_endurance.isdigit():
            updates.append("desired endurance = %s")
            params.append(desired_endurance)
    else:
        print("Invalid ")

    execute_update(conn, "Health_Metrics", updates, params, member_id)


def execute_update(conn, table, updates, params, member_id):
    cursor = conn.cursor()
    query = f"UPDATE {table} SET " + ", ".join(updates)
    query += " WHERE id = %s;" #not sure about this line
    params.append(member_id)

    try:
        cursor.execute(query, params)
        conn.commit()
        print("Updates have been applied.")
    except psycopg2.Error as error:
        conn.rollback()
        print(f"Error updating info {error}")
    finally:
        cursor.close()


def display_member_info(conn, member_id):
    cursor = conn.cursor()

    cursor.execute("""
    SELECT height, weight, desired_weight, endurance_importance, strength_importance
    FROM Health_Metrics
    WHERE member_id = %s; 
    """, (member_id,))
    health_metrics = cursor.fetchone() #these might need to be modified
    print(health_metrics)
    if health_metrics:
        print("Member Metrics:")
        print(f"Height: {health_metrics[0]} cm")
        print(f"Weight: {health_metrics[1]} lbs")
        print(f"Desired Weight: {health_metrics[2]} lbs")
        print(f"Endurance Importance: {health_metrics[3]}")
        print(f"Strength Importance: {health_metrics[4]}")
    else:
        print("No member metrics found for this member")
    

    #Add routines at some point

    cursor.close()
    return health_metrics