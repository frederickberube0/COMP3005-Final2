import re
import psycopg2.extras

# def set_trainer_availability(conn, trainerid: str):
    # """
    # Sets the availability for a trainer.
    # """
    # valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')  # HH:MM format

    # day_of_week = ""
    # start_time = ""
    # end_time = ""

    # # Validate day of the week
    # while day_of_week not in valid_days:
    #     day_of_week = input("Enter day of the week (Monday, Tuesday, etc.): ")
    #     if day_of_week not in valid_days:
    #         print("Invalid day of the week. Please enter a valid day (e.g., Monday, Tuesday).")

    # # Validate start time
    # while not time_pattern.match(start_time):
    #     start_time = input("Enter start time (HH:MM): ")
    #     if not time_pattern.match(start_time):
    #         print("Invalid start time. Please enter time in HH:MM format.")

    # # Validate end time
    # while not time_pattern.match(end_time):
    #     end_time = input("Enter end time (HH:MM): ")
    #     if not time_pattern.match(end_time):
    #         print("Invalid end time. Please enter time in HH:MM format.")

    # # SQL to insert/update trainer availability
    # query = """
    # INSERT INTO Trainer_Availability (id, day_of_week, start_time, end_time)
    # VALUES (%s, %s, %s, %s)
    # ON CONFLICT (id, day_of_week) DO UPDATE
    # SET start_time = EXCLUDED.start_time,
    #     end_time = EXCLUDED.end_time;
    # """

    # with conn.cursor() as cur:
    #     cur.execute(query, (trainerid, day_of_week, start_time, end_time))
    #     conn.commit()

    # print("Trainer availability set successfully.")

def set_trainer_availability(conn, trainer_id, day_of_week, start_time, end_time):
    """
    Sets the availability for a trainer.
    """
    query = """
    INSERT INTO trainer_availiblity (id, day_of_week, start_time, end_time)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (id, day_of_week) DO UPDATE
    SET start_time = EXCLUDED.start_time,
        end_time = EXCLUDED.end_time;
    """
    with conn.cursor() as cur:
        cur.execute(query, (trainer_id, day_of_week, start_time, end_time))


def get_trainer_availability(conn, trainer_id):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Initialize the availability dictionary for all days of the week
        availability = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

        # Fetch the general availability of the trainer
        cur.execute("""
            SELECT day_of_week, EXTRACT(HOUR FROM start_time) AS start_hour, EXTRACT(HOUR FROM end_time) AS end_hour
            FROM Trainer_Availiblity
            WHERE id = %s
        """, (trainer_id,))
        availability_data = cur.fetchall()

        # Update the availability dictionary with the hours the trainer is generally available
        for data in availability_data:
            day, start_hour, end_hour = data['day_of_week'], int(data['start_hour']), int(data['end_hour'])
            availability[day] = list(range(start_hour, end_hour + 1))  # +1 because range is exclusive of the end value

        # Fetch the hours when the trainer is booked for events
        cur.execute("""
            SELECT day_of_week, EXTRACT(HOUR FROM time) AS event_hour
            FROM Event
            WHERE staff_id = %s
        """, (trainer_id,))
        events_data = cur.fetchall()

        # Remove the hours when the trainer is booked from the availability
        for event in events_data:
            day, event_hour = event['day_of_week'], int(event['event_hour'])
            if event_hour in availability[day]:
                availability[day].remove(event_hour)

    print(availability)
    return availability






def create_class(conn, date, time, room_id, trainer_id):
    """
    Creates a new group class event.
    """
    with conn.cursor() as cur:
        query = """ 
        INSERT INTO Event (date, time, room_id, trainer_id, type) 
        VALUES (%s, %s, %s, %s, 'Group')
        """
        cur.execute(query, (date, time, room_id, trainer_id))
        conn.commit()
    print("New group class created successfully!")
