def find_available_room(conn, day_of_week: str, time: str):
    """
    Find an available room for the specified day of the week and time.

    Parameters:
    - day_of_week: Day of the week as 'Monday', 'Tuesday', etc.
    - time: HH:MM formatted time
    """
    available_rooms = []
    with conn.cursor() as cur:
        query = """
        SELECT r.id
        FROM Room r
        JOIN Room_Availability ra ON ra.room_id = r.id
        WHERE ra.day_of_week = %s
        AND ra.start_time <= %s AND ra.end_time > %s
        AND r.id NOT IN (
            SELECT e.room_id
            FROM Event e
            WHERE e.day_of_week = %s AND e.time = %s
        )
        """
        cur.execute(query, (day_of_week, time, time, day_of_week, time))
        available_rooms = cur.fetchall()
        available_rooms = [room_id[0] for room_id in available_rooms]

    return available_rooms


def create_new_group_class(conn): #Might modify to add a class title perhaps? Like Pilates, Yoga, etc.
    date = input("Enter the date for the new class (YYYY-MM-DD): ")
    time = input ("Enter the time for the new class (HH:MM): ")

    available_rooms = finds_available_room(conn, date, time)
    if not available_rooms:
        print("No rooms available for the specified date and time.")
        return
    room_id = available_rooms[0]

    available_trainers = find_available_trainer(conn, date, time)
    if not available_trainers:
        print("No trainers available for the specified date and time.")
        return
    trainer_id = available_trainers[0]

    with conn.cursor() as cur: 
        query = """ 
        INSERT INTO Event (date, time, room_id, trainer_id, type) 
        VALUES (%s, %s, %s, %s, 'Group')
        """
        cur.execute(query, (date, time, room_id, trainer_id))
        conn.commit()
    print("New group class created successfully!")


def find_available_trainer(conn, date: str, time: str):
    """
    Find an available trainer for the specified date and time.

    Parameters:
    - date: YYYY-MM-DD
    - time: HH:MM
    """
    available_trainers = []
    with conn.cursor() as cur:
        query = """
        SELECT t.id
        FROM Trainer t
        WHERE t.id NOT IN (
            SELECT e.trainer_id
            FROM Event e
            WHERE e.date = %s AND e.time = %s
        )
        """
        cur.execute(query, (date, time))
        available_trainers = cur.fetchall()
        available_trainers = [trainer_id[0] for trainer_id in available_trainers]

    return available_trainers