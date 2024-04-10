from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import psycopg2
from src.admins.admin_functions import get_hash, safe_int_input, is_valid_email, is_unique_email
from src.members.members_functions import update_member_info, update_fitness_goals, display_member_info
from src.health_club_management.management_functions import find_available_trainer, find_available_room, create_new_group_class
from src.trainers.trainers_functions import create_class, set_trainer_availability, get_trainer_availability

app = Flask(__name__)
app.secret_key = 'secret'

db_params = {
    'dbname': 'ProjectV2',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': "5432",
}

@app.route('/create_event', methods=['POST'])
def create_event():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403

    data = request.get_json()
    day_of_week = data['day']
    time = data['time']
    title = "PT Session" 

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("""
            SELECT r.id, r.number, r.capacity
            FROM Room r
            WHERE r.id NOT IN (
                SELECT e.room_id
                FROM Event e
                WHERE e.day_of_week = %s AND e.time = %s
            ) AND EXISTS (
                SELECT 1
                FROM Room_Availability ra
                WHERE ra.room_id = r.id AND ra.day_of_week = %s AND %s BETWEEN ra.start_time AND ra.end_time
            )
        """, (day_of_week, time, day_of_week, time))

        rooms = [{'id': row[0], 'number': row[1], 'capacity': row[2]} for row in cur.fetchall()]

        if not rooms:
            return jsonify({'error': 'No available rooms'}), 400

        room_id = rooms[0]['id'] 

        cur.execute("SELECT preferred_trainer_id FROM Members WHERE id = %s", (user_id,))
        staff_id = cur.fetchone()
        if staff_id is not None:
            staff_id = staff_id[0]
        else:
            return jsonify({'error': 'Preferred trainer not found'}), 404

        cur.execute("""
            INSERT INTO Event (title, staff_id, room_id, time, day_of_week, type)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING event_id
        """, ("PT Session", staff_id, room_id, time, day_of_week, 'Individual'))
        event_id = cur.fetchone()[0]


        cur.execute("INSERT INTO Attendees (attendee_id, event_id) VALUES (%s, %s)", (user_id, event_id))
        
        conn.commit()

        return jsonify({'success': True, 'event_id': event_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/set_preferred_trainer', methods=['POST'])
def set_preferred_trainer():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    data = request.get_json()
    trainer_id = data['trainerId']
    member_id = session['user_id']

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("UPDATE Members SET preferred_trainer_id = %s WHERE id = %s", (trainer_id, member_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"success": "Preferred trainer updated successfully"})

@app.route('/search_trainers')
def search_trainers():
    query = request.args.get('query', '')
    if query == '':
        return jsonify([])
    

    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    
    sql_query = """SELECT Trainers.name, Trainers.id, Users.picture_link
FROM Trainers
JOIN Users ON Trainers.id = Users.id
WHERE Trainers.name ILIKE %s""" 
    cur.execute(sql_query, ('%' + query + '%',))
    results = cur.fetchall()
    print(results)
    

    members = [{'name': row[0], 'id': row[1], 'picture_link': row[2]} for row in results]
    
    cur.close()
    conn.close()
    
    return jsonify(members)

@app.route('/search_members')
def search_members():
    query = request.args.get('query', '')
    if query == '':
        return jsonify([])
    
    conn = psycopg2.connect(**db_params) 
    cur = conn.cursor()
    
    sql_query = """SELECT Members.name, Members.id, Users.picture_link
FROM Members
JOIN Users ON Members.id = Users.id
WHERE Members.name ILIKE %s""" 
    cur.execute(sql_query, ('%' + query + '%',))
    results = cur.fetchall()
    print(results)
    
    members = [{'name': row[0], 'id': row[1], 'picture_link': row[2]} for row in results]
    
    cur.close()
    conn.close()
    
    return jsonify(members)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Email and password are required", "error")
            return render_template('login.html')

        try:
            conn = psycopg2.connect(**db_params)
            with conn.cursor() as cur:
                cur.execute("SELECT id, role, password FROM Users WHERE email = %s", (email,))
                user = cur.fetchone()

                if user and get_hash(password) == user[2]: 
                    session['user_id'] = user[0]
                    session['role'] = user[1]

                    if user[1] == 'Member':
                        return redirect(url_for('member_dashboard'))
                    elif user[1] == 'Trainer':
                        return redirect(url_for('trainer_dashboard'))
                    elif user[1] == 'Admin':
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('main_menu'))
                else:
                    flash("Login failed. Check your email and password and try again.", "error")
                    return render_template('login.html')

        except psycopg2.Error as e:
            flash("Database connection failed", "error")
            return render_template('login.html')



@app.route('/')
def main_menu():
    return render_template('main_menu.html')

@app.route('/register', methods=['GET', 'POST'])
def handle_register():
    if request.method == 'POST':
        try:
            conn = psycopg2.connect(**db_params)
            cur = conn.cursor()

            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')  

            if not email or not is_valid_email(conn, email):
                flash("Invalid email", "error")
                return render_template('register.html')
            if not password:
                flash("Invalid password", "error")
                return render_template('register.html')

            password_hash = get_hash(password)
            session['email'] = email
            session['name'] = name
            session['password_hash'] = password_hash
            print(session['name'], session['email'], session['password_hash'])
            # cur.execute("INSERT INTO Users (email, password, role, picture_link) VALUES (%s, %s, 'Member', 'profile_pictures/template.png') RETURNING id", (email, password_hash))
            # user_id = cur.fetchone()[0]
            # conn.commit()

            # session['user_id'] = user_id

        except psycopg2.Error as e:
            conn.rollback() 
            flash("Email already in use", "error")
            return render_template('register.html')
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('show_health_info'))
    else:
        return render_template('register.html')


        
@app.route('/health_info')
def show_health_info():
    return render_template('health_info.html')

@app.route('/submit_health_info', methods=['POST'])
def submit_health_info():
    if 'email' not in session or 'password_hash' not in session:
        flash("You need to log in first.")
        return redirect(url_for('login'))
    
    age = int(request.form['age'])
    gender = request.form['gender']
    height = int(request.form['height'])
    weight = int(request.form['weight'])
    cardio_importance = int(request.form['cardio'])
    strength_importance = int(request.form['strength'])
    desired_weight = int(request.form.get('dweight'))
    
    try:
        conn = psycopg2.connect(**db_params)  
        cur = conn.cursor()

        cur.execute("INSERT INTO Users (email, password, role, picture_link) VALUES (%s, %s, %s, %s) RETURNING id",
                    (session['email'], session['password_hash'], 'Member', 'profile_pictures/template.png'))
        user_id = cur.fetchone()[0]
        print(user_id, height, weight, cardio_importance, strength_importance, desired_weight)
        session['user_id'] = user_id
        cur.execute("INSERT INTO Members (id, name, age, gender, preferred_trainer_id) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, session['name'], age, gender, 3))
        cur.execute("""
            INSERT INTO Health_Metrics (member_id, height, weight, endurance_importance, strength_importance, desired_weight)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, height, weight, cardio_importance, strength_importance, desired_weight))
        print("3")
        conn.commit()
        flash("Health information submitted successfully.")
    except psycopg2.Error as e:
        conn.rollback()
        flash("Database error: " + str(e))
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('member_dashboard'))




@app.route('/update_member_info', methods=['POST'])
def handle_update_member_info():
    data = request.json
    member_id = data.get('member_id')
    try:
        conn = psycopg2.connect(**db_params)
        update_member_info(conn, member_id, data)  
        conn.close()
        return jsonify({"message": "Member info updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/display_member_info/<int:member_id>', methods=['GET'])
def handle_display_member_info(member_id):
    print(member_id)
    try:
        conn = psycopg2.connect(**db_params)
        member_info = display_member_info(conn, int(member_id))  
        print(member_info)
        conn.close()
        return jsonify(member_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/member_dashboard_from_trainer/<int:memberid>', methods=['GET'])
def member_dashboard_from_trainer(memberid):
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or role == "Member":
        return redirect(url_for('login'))

    member_name = None
    health_metrics = None
    picture_link = None
    member_classes = None
    
    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM Members WHERE id = %s", (memberid,))
            member_name_result = cur.fetchone()
            if member_name_result:
                member_name = member_name_result[0]
            
            cur.execute("SELECT picture_link FROM Users WHERE id = %s", (memberid,))
            picture_link = cur.fetchone()[0]
            
            health_metrics = display_member_info(conn, memberid)
            
            cur.execute("""
                SELECT e.time, e.day_of_week, e.type
                FROM Attendees a
                JOIN Event e ON a.event_id = e.event_id
                WHERE a.attendee_id = %s AND e.staff_id = %s
            """, (memberid, user_id))
            member_classes = cur.fetchall()

    except Exception as e:
        print(f"Error retrieving member info: {e}")
    finally:
        conn.close()

    return render_template('member_dashboard_from_trainer.html', member_name=member_name, health_metrics=health_metrics, image_link=picture_link, member_classes=member_classes)

@app.route('/member_dashboard', methods=['GET'])
def member_dashboard():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))

    member_name = None
    health_metrics = None
    picture_link = None
    upcoming_classes = []
    exercises_by_day_type = {'Push Day': [], 'Pull Day': [], 'Leg Day': []}

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM Members WHERE id = %s", (user_id,))
        member_name_result = cur.fetchone()
        member_name = member_name_result[0] if member_name_result else None

        cur.execute("SELECT picture_link FROM Users WHERE id = %s", (user_id,))
        picture_link = cur.fetchone()[0]

        cur.execute("""
            SELECT Event.day_of_week, Event.time, Trainers.name, Room.number, Event.event_id, Event.type, Event.title
            FROM Event
            JOIN Attendees ON Event.event_id = Attendees.event_id
            JOIN Trainers ON Event.staff_id = Trainers.id
            JOIN Room ON Event.room_id = Room.id
            WHERE Attendees.attendee_id = %s
            ORDER BY Event.day_of_week, Event.time
        """, (user_id,))
        upcoming_classes = [{'day': row[0], 'time': row[1].strftime('%H:%M'), 'trainer_name': row[2], 'room_number': row[3], 'event_id': row[4], 'type': row[5], 'title': row[6]} for row in cur.fetchall()]

        health_metrics = display_member_info(conn, user_id)

        for day_type in exercises_by_day_type.keys():
            cur.execute("""
                SELECT e.name, re.reps, re.sets, re.personal_record, re.routine_exercise_id
                FROM Routine_Exercises re
                JOIN Routines r ON re.routine_id = r.routine_id
                JOIN Exercises e ON re.exercise_id = e.exercise_id
                WHERE r.member_id = %s AND r.day_type = %s
            """, (user_id, day_type))
            exercises_by_day_type[day_type] = [{'name': row[0], 'reps': row[1], 'sets': row[2], 'personal_best': row[3], 'routine_exercise_id': row[4]} for row in cur.fetchall()]

    except Exception as e:
        print(f"Error retrieving member dashboard data: {e}")
    finally:
        if conn:
            conn.close()

    return render_template('member_dashboard.html', member_name=member_name, health_metrics=health_metrics, picture_link=picture_link, upcoming_classes=upcoming_classes, exercises_by_day_type=exercises_by_day_type)



@app.route('/trainer_dashboard', methods=['GET'])
def trainer_dashboard():
    user_id = session.get('user_id')
    member_name = None
    availability = None
    picture_link = None
    conn = psycopg2.connect(**db_params)
    try:
        
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM Trainers WHERE id = %s", (user_id,))
            member_name_result = cur.fetchone()
            cur.execute("SELECT picture_link FROM Users WHERE id = %s", (user_id,))
            picture_link = cur.fetchone()[0]
            if member_name_result:
                member_name = member_name_result[0]
            
        availability = get_trainer_availability(conn, user_id)
    except Exception as e:
        print(f"Error retrieving member info: {e}")
    finally:
        conn.close()

    role = session.get('role')
    if not user_id or role == 'Member':
        return redirect(url_for('login'))
    
    print(member_name)
    return render_template('trainer_dashboard.html',member_name=member_name, availability=availability, image_link=picture_link)



@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    user_id = session.get('user_id')
    user_role = session.get('role')
    admin_name = None
    picture_link = None

    if not user_id or user_role != 'Admin':
        flash("Access restricted to administrators.", "error")
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM Admin WHERE id = %s", (user_id,))
            admin_name_result = cur.fetchone()
            cur.execute("SELECT picture_link FROM Users WHERE id = %s", (user_id,))
            picture_link = cur.fetchone()[0]
            if admin_name_result:
                admin_name = admin_name_result[0]

    except Exception as e:
        flash(f"Database error: {e}", "error")
        return render_template('login.html')
    finally:
        conn.close()

    return render_template('admin_dashboard.html', admin_name=admin_name, image_link=picture_link)

@app.route('/create_group_event', methods=['POST'])
def create_group_event():
    if 'role' not in session or session['role'] != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    day_of_week = request.form['day']
    time = request.form['time']
    trainer_id = request.form['trainer_id']  
    title = request.form['className']

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        room_id = request.form['room_id']

        cur.execute("""
            INSERT INTO Event (title, staff_id, room_id, time, day_of_week, type)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING event_id
        """, (title, trainer_id, room_id, time, day_of_week, 'Group'))
        event_id = cur.fetchone()[0]



        conn.commit()
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/manage_group_classes', methods=['GET'])
def manage_group_classes():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    group_classes = []
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
            SELECT Event.event_id, Trainers.name, Room.number, Event.day_of_week, Event.time
            FROM Event
            JOIN Trainers ON Event.staff_id = Trainers.id
            JOIN Room ON Event.room_id = Room.id
            WHERE Event.type = 'Group'
        """)
        group_classes = cur.fetchall()
    except Exception as e:
        flash(f"Database error: {e}", "error")
    finally:
        if conn:
            conn.close()

    return render_template('manage_group_classes.html', group_classes=group_classes)

@app.route('/get_available_trainers')
def get_available_trainers():
    day = request.args.get('day')
    time = request.args.get('time')

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
            SELECT Trainers.id, Trainers.name
            FROM Trainers
            JOIN Trainer_Availiblity ON Trainers.id = Trainer_Availiblity.id
            WHERE Trainer_Availiblity.day_of_week = %s AND %s BETWEEN Trainer_Availiblity.start_time AND Trainer_Availiblity.end_time
            EXCEPT
            SELECT Event.staff_id, Trainers.name
            FROM Event
            JOIN Trainers ON Event.staff_id = Trainers.id
            WHERE Event.day_of_week = %s AND Event.time = %s
        """, (day, time, day, time))
        available_trainers = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
        return jsonify(available_trainers)
    except Exception as e:
        print(f"Error fetching available trainers: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/view_room_bookings/<int:room_id>')
def view_room_bookings(room_id):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
            SELECT e.event_id, e.day_of_week, e.time, t.name as trainer_name, e.type
            FROM Event e
            JOIN Trainers t ON e.staff_id = t.id
            WHERE e.room_id = %s
        """, (room_id,))
        bookings = [{
            'event_id': row[0],
            'day_of_week': row[1],
            'time': row[2],
            'trainer_name': row[3],
            'type': row[4]
        } for row in cur.fetchall()]
    except Exception as e:
        flash(f"Database error: {e}", "error")
        return render_template('admin_dashboard.html')
    finally:
        if conn:
            conn.close()

    return render_template('view_room_bookings.html', bookings=bookings, room_id=room_id)


@app.route('/get_available_rooms', methods=['GET']) 
def get_available_rooms():
    day = request.args.get('day')
    time = request.args.get('time')

    if not day or not time:
        return jsonify([]), 400

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("""
            SELECT r.id, r.number, r.capacity
            FROM Room r
            WHERE r.id NOT IN (
                SELECT e.room_id
                FROM Event e
                WHERE e.day_of_week = %s AND e.time = %s
            ) AND EXISTS (
                SELECT 1
                FROM Room_Availability ra
                WHERE ra.room_id = r.id AND ra.day_of_week = %s AND %s BETWEEN ra.start_time AND ra.end_time
            )
        """, (day, time, day, time))

        rooms = [{'id': row[0], 'number': row[1], 'capacity': row[2]} for row in cur.fetchall()]
        return jsonify(rooms)
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



@app.route('/manage_rooms', methods=['GET'])
def manage_rooms():
    if 'role' not in session or session['role'] != 'Admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("SELECT id, number, capacity FROM Room")
        rooms = cur.fetchall()
    except Exception as e:
        flash(f"Database error: {e}", "error")
        return render_template('admin_dashboard.html')
    finally:
        if conn:
            conn.close()

    return render_template('manage_rooms.html', rooms=rooms)

@app.route('/add_room', methods=['POST'])
def add_room():
    room_number = request.form.get('room_number')
    capacity = request.form.get('capacity')

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("INSERT INTO Room (number, capacity) VALUES (%s, %s)", (room_number, capacity))
        conn.commit()
        flash("Room added successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to add room: {e}", "error")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('manage_rooms'))

@app.route('/delete_room/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if 'role' not in session or session['role'] != 'Admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("DELETE FROM Room WHERE id = %s", (room_id,))
        conn.commit()
        flash("Room deleted successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete room: {e}", "error")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('manage_rooms'))

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    room_id = request.form.get('room_id')

    if not room_id:
        flash("Missing room ID.", "error")
        return redirect(url_for('manage_rooms'))

    if 'role' not in session or session['role'] != 'Admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("DELETE FROM Event WHERE event_id = %s", (event_id,))
        conn.commit()
        flash("Event deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete event: {e}", "error")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('view_room_bookings', room_id=room_id))


@app.route('/edit_health_info', methods=['GET', 'POST'])
def edit_health_info():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        if request.method == 'POST':
            height = request.form.get('height')
            weight = request.form.get('weight')
            desired_weight = request.form.get('dweight')
            cardio = request.form.get('cardio')
            strength = request.form.get('strength')
            
            cur.execute("""
                UPDATE Health_Metrics
                SET height = %s, weight = %s, desired_weight = %s,
                    endurance_importance = %s, strength_importance = %s
                WHERE member_id = %s
            """, (height, weight, desired_weight, cardio, strength, user_id))
            conn.commit()
            print(height, weight, desired_weight, cardio, strength, user_id)
            flash("Health information updated successfully.", "success")
            return redirect(url_for('member_dashboard'))
        else:
            cur.execute("SELECT * FROM Health_Metrics WHERE member_id = %s", (user_id,))
            health_metrics = cur.fetchone()
            return render_template('edit_health_info.html', health_metrics=health_metrics)
    except Exception as e:
        conn.rollback()
        flash("An error occurred: " + str(e), "error")
        return redirect(url_for('member_dashboard'))
    finally:
        cur.close()
        conn.close()



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/availability', methods=['GET', 'POST'])
def availability():
    trainer_id = session.get('user_id')
    if not trainer_id:
        flash("You must be logged in to set availability.", "error")
        return redirect(url_for('login'))

    availability = {}
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        if request.method == 'GET':
            cur.execute("""
                SELECT day_of_week, start_time, end_time
                FROM Trainer_Availiblity
                WHERE id = %s
            """, (trainer_id,))
            availability = {row[0]: {'start_time': row[1].strftime('%H:%M'), 'end_time': row[2].strftime('%H:%M')}
                            for row in cur.fetchall()}
            print("Fetched availability:", availability)

        elif request.method == 'POST':
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                start_time = request.form.get(f'{day.lower()}_start')
                end_time = request.form.get(f'{day.lower()}_end')
                if start_time and end_time:
                    cur.execute("""
                        INSERT INTO Trainer_Availiblity (id, day_of_week, start_time, end_time)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id, day_of_week) DO UPDATE
                        SET start_time = EXCLUDED.start_time, end_time = EXCLUDED.end_time
                    """, (trainer_id, day, start_time, end_time))
            conn.commit()
            flash("Availability set successfully!", "success")
            return redirect(url_for('trainer_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred while setting your availability: {str(e)}", "error")
        print("Error:", e)
    finally:
        cur.close()
        conn.close()

    return render_template('set_availability.html', availability=availability)


@app.route('/set_availability', methods=['GET', 'POST'])
def set_availability():
    trainer_id = session.get('user_id') 
    if not trainer_id:
        flash("You must be logged in to set availability.", "error")
        return redirect(url_for('login'))

    availability = {}

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        if request.method == 'GET':
            cur.execute("""
                SELECT day_of_week, start_time, end_time
                FROM Trainer_Availiblity
                WHERE id = %s
            """, (trainer_id,))
            availability = {row[0]: {'start_time': row[1].strftime('%H:%M'), 'end_time': row[2].strftime('%H:%M')}
                            for row in cur.fetchall()}

        elif request.method == 'POST':
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                start_time = request.form.get(f'{day.lower()}_start')
                end_time = request.form.get(f'{day.lower()}_end')
                if start_time and end_time:
                    cur.execute("""
                        INSERT INTO Trainer_Availiblity (id, day_of_week, start_time, end_time)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id, day_of_week) DO UPDATE
                        SET start_time = EXCLUDED.start_time, end_time = EXCLUDED.end_time
                    """, (trainer_id, day, start_time, end_time))
            conn.commit()
            flash("Availability set successfully!", "success")
            return redirect(url_for('trainer_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred while setting your availability: {str(e)}", "error")
    finally:
        cur.close()
        conn.close()

    return render_template('set_availability.html', availability=availability)




@app.route('/class_scheduler')
def class_scheduler():
    member_id = session.get('user_id')
    if not member_id:
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("SELECT preferred_trainer_id FROM Members WHERE id = %s", (member_id,))
        trainer_id = cur.fetchone()[0]
        if not trainer_id:
            return jsonify({"error": "No preferred trainer set"}), 400

      
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        hours = range(9, 18) 
        availability = {day: {f"{hour}:00": 'bg-gray-400' for hour in hours} for day in days}

        cur.execute("""
            SELECT day_of_week, start_time, end_time 
            FROM Trainer_Availiblity 
            WHERE id = %s
        """, (trainer_id,))
        for row in cur.fetchall():
            day, start_time, end_time = row
            for hour in range(start_time.hour, end_time.hour + 1): 
                time_str = f"{hour}:00"
                if time_str in availability[day]: 
                    availability[day][time_str] = 'bg-green-200'

        cur.execute("""
            SELECT day_of_week, time
            FROM Event 
            WHERE staff_id = %s
        """, (trainer_id,))
        for row in cur.fetchall():
            day, event_time = row
            time_str = event_time.strftime("%H:%M")
            if time_str in availability[day]:
                availability[day][time_str] = 'bg-red-900'

    except Exception as e:
        print(f"Error retrieving trainer availability: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

    return render_template('class_scheduler.html', availability=availability, days=days, hours=hours)

@app.route('/set_room_availability/<int:room_id>', methods=['GET'])
def set_room_availability(room_id):
    if 'role' not in session or session['role'] != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    room_info = {'room_id': room_id, 'room_availability': {}}
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
            SELECT day_of_week, start_time, end_time 
            FROM Room_Availability 
            WHERE room_id = %s
        """, (room_id,))
        room_info['room_availability'] = {
            row[0]: {'start_time': row[1].strftime('%H:%M'), 'end_time': row[2].strftime('%H:%M')}
            for row in cur.fetchall()
        }
    except Exception as e:
        flash(f"Database error: {e}", "error")
        return redirect(url_for('manage_rooms'))
    finally:
        cur.close()
        conn.close()

    return render_template('set_room_availability.html', room_info=room_info)


@app.route('/cancel_class/<int:event_id>', methods=['POST'])
def cancel_class(event_id):
    if 'user_id' not in session:
        flash("You must be logged in to cancel classes.", "error")
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("DELETE FROM Attendees WHERE attendee_id = %s AND event_id = %s", (session['user_id'], event_id))
        conn.commit()
        flash("Class cancelled successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to cancel class: {e}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('member_dashboard'))


@app.route('/submit_room_availability/<int:room_id>', methods=['POST'])
def submit_room_availability(room_id):
    if 'role' not in session or session['role'] != 'Admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("DELETE FROM Room_Availability WHERE room_id = %s", (room_id,))
        print(f"Cleared existing availability for room_id: {room_id}")

        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            start_time = request.form.get(f"{day.lower()}_start")
            end_time = request.form.get(f"{day.lower()}_end")

            print(f"Processing {day}: Start Time: {start_time}, End Time: {end_time}")

            if start_time and end_time: 
                cur.execute("""
                    INSERT INTO Room_Availability (room_id, day_of_week, start_time, end_time)
                    VALUES (%s, %s, %s, %s)
                """, (room_id, day, start_time, end_time))
                print(f"Inserted {day} availability for Room ID {room_id}: {start_time} to {end_time}")

        conn.commit()
        flash("Room availability updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Exception occurred: {e}")
        flash(f"Failed to update room availability: {e}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('manage_rooms'))

@app.route('/payment/<int:event_id>', methods=['GET'])
def show_payment_form(event_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("SELECT staff_id, room_id, time, day_of_week FROM Event WHERE event_id = %s", (event_id,))
        event_details = cur.fetchone()
        if not event_details:
            flash("Event not found.", "error")
            return redirect(url_for('register_group_class'))
        return render_template('payment_process.html', event_id=event_id, event_details=event_details)
    except Exception as e:
        print("Error fetching event details:", e)
        flash(f"Database error: {e}", "error")
        return redirect(url_for('register_group_class'))
    finally:
        cur.close()
        conn.close()


@app.route('/process_payment', methods=['POST'])
def process_payment():
    member_id = session.get('user_id')
    if not member_id:
        return jsonify({'error': 'User not logged in'}), 403

    data = request.get_json()
    event_id = data.get('event_id')
    credit_card_number = data.get('credit_card_number')
    price_paid = data.get('price_paid')

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO Payments (member_id, event_id, price_paid, credit_card_number)
            VALUES (%s, %s, %s, %s)
            RETURNING payment_id
        """, (member_id, event_id, price_paid, credit_card_number))
        payment_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({'success': True, 'payment_id': payment_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/view_payments', methods=['GET'])
def view_payments():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.payment_id, p.time_of_purchase, p.price_paid, m.name, e.day_of_week, e.time
            FROM Payments p
            JOIN Members m ON p.member_id = m.id
            JOIN Event e ON p.event_id = e.event_id
            ORDER BY p.time_of_purchase DESC
        """)
        payments = cur.fetchall()
    except Exception as e:
        flash(f"Database error: {e}", "error")
        return render_template('admin_dashboard.html')
    finally:
        cur.close()
        conn.close()

    return render_template('view_payments.html', payments=payments)


@app.route('/register_group_class')
def register_group_class():
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
            SELECT e.event_id, e.day_of_week, e.time, t.name as trainer_name, r.number, e.title
            FROM Event e
            JOIN Trainers t ON e.staff_id = t.id
            JOIN Room r ON e.room_id = r.id
            WHERE e.type = 'Group'
        """)
        event_rows = cur.fetchall()
        group_classes = [{
            'event_id': row[0],
            'day_of_week': row[1],
            'time': row[2].strftime('%H:%M'), 
            'trainer_name': row[3],
            'number': row[4],
            'title': row[5]
        } for row in event_rows]
        
        return render_template('register_group_class.html', group_classes=group_classes)
    except Exception as e:
        print(f"Database error: {str(e)}")
        return f"An error occurred: {str(e)}", 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()




@app.route('/register_for_class/<int:class_id>', methods=['GET', 'POST'])
def register_for_class(class_id):
    if 'user_id' not in session:
        flash("You must be logged in to register for classes.", "error")
        return redirect(url_for('login'))
    user_id = session.get('user_id')
   
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
            SELECT count(*) FROM Attendees WHERE event_id = %s
        """, (class_id,))
        count = cur.fetchone()[0]
       
        cur.execute("""
            SELECT capacity FROM Room JOIN Event ON Room.id = Event.room_id WHERE Event.event_id = %s
        """, (class_id,))
        capacity = cur.fetchone()[0]
        if count >= capacity:
            flash("This class is already full.", "error")
            return redirect(url_for('register_group_class'))

        cur.execute("""
            INSERT INTO Attendees (attendee_id, event_id) VALUES (%s, %s)
        """, (user_id, class_id))
        conn.commit()
        flash("Successfully registered for the class.", "success")
        return redirect(url_for('show_payment_form', event_id=class_id))  
    except Exception as e:
        conn.rollback()
        flash(f"Error registering for the class: {str(e)}", "error")
    finally:
        if conn:
            conn.close()
    return redirect(url_for('register_group_class'))


@app.route('/maintenance')
def maintenance():

    day_of_week = request.args.get('day_of_week') 

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        query = """
            SELECT e.equipment_id, e.equipment_name, ms.frequency, ms.day_of_week, ms.time
            FROM Equipment e
            JOIN Maintenance_Schedule ms ON e.equipment_id = ms.id
        """
        
        if day_of_week:
            query += " WHERE ms.day_of_week = %s"
            cur.execute(query, (day_of_week,))
        else:
            cur.execute(query)

        equipments = [{
            'equipment_id': row[0],
            'equipment_name': row[1],
            'frequency': row[2],
            'day_of_week': row[3],
            'time': row[4].strftime('%H:%M')  
        } for row in cur.fetchall()]
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        equipments = [] 
    finally:
        if conn:
            conn.close()

    return render_template('maintenance.html', equipments=equipments, selected_day=day_of_week)

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("""
            SELECT e.equipment_id, e.equipment_name, ms.frequency, ms.day_of_week, ms.time
            FROM Equipment e
            JOIN Maintenance_Schedule ms ON e.equipment_id = ms.id
            ORDER BY e.equipment_name
        """)
        equipments = [{
            'equipment_id': row[0], 
            'equipment_name': row[1],
            'frequency': row[2],
            'day_of_week': row[3],
            'time': row[4].strftime('%H:%M') 
        } for row in cur.fetchall()]
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        equipments = [] 
    finally:
        if conn:
            conn.close()

    return render_template('maintenance.html', equipments=equipments)




@app.route('/add_equipment', methods=['GET'])
def add_equipment_form():
    return render_template('add_equipment.html')

@app.route('/add_equipment', methods=['POST'])
def add_equipment():
    equipment_name = request.form.get('equipment_name')
    frequency = request.form.get('frequency')
    day_of_week = request.form.get('day_of_week')
    time = request.form.get('time')
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("INSERT INTO Equipment (equipment_name) VALUES (%s) RETURNING equipment_id", (equipment_name,))
        equipment_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO Maintenance_Schedule (id, day_of_week, time, frequency)
            VALUES (%s, %s, %s, %s)
        """, (equipment_id, day_of_week, time, frequency))

        conn.commit()
        flash("Equipment and maintenance schedule added successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to add equipment and schedule: {str(e)}", "error")
    finally:
        if conn:
            conn.close()
    return redirect(url_for('maintenance'))


@app.route('/get_routine', methods=['POST'])
def get_routine():
    member_id = session.get('user_id')
    if not member_id:
        return jsonify({'error': 'Not logged in'}), 403

    day_type = request.form.get('day_type')

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("""
            SELECT routine_id FROM Routines
            WHERE member_id = %s AND day_type = %s
        """, (member_id, day_type))
        routine = cur.fetchone()
        if not routine:
            return jsonify({'error': 'Routine not found'}), 404

        cur.execute("""
            SELECT e.name, re.reps, re.sets, re.personal_record
            FROM Routine_Exercises re
            JOIN Exercises e ON re.exercise_id = e.exercise_id
            WHERE re.routine_id = %s
        """, (routine[0],))
        exercises = [{'name': row[0], 'reps': row[1], 'sets': row[2], 'pr': row[3]} for row in cur.fetchall()]

        return jsonify({'success': True, 'exercises': exercises})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/get_routine_by_day', methods=['GET', 'POST'])
def get_routine_by_day():
    member_id = session.get('user_id')
    if not member_id:
        return jsonify({'error': 'User not logged in'}), 403

    if request.method == 'POST':
        day_type = request.form['day_type']

        conn = psycopg2.connect(**db_params)
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT e.name, re.reps, re.sets, re.personal_record
                FROM Routine_Exercises re
                JOIN Routines r ON re.routine_id = r.routine_id
                JOIN Exercises e ON re.exercise_id = e.exercise_id
                WHERE r.member_id = %s AND r.day_type = %s
            """, (member_id, day_type))
            exercises = cur.fetchall()
            return render_template('member_dashboard.html', routine_exercises=exercises, selected_day_type=day_type)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()
            conn.close()
    else:
        return redirect(url_for('member_dashboard'))



@app.route('/delete_equipment/<int:equipment_id>', methods=['POST'])
def delete_equipment(equipment_id):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("DELETE FROM Equipment WHERE equipment_id = %s", (equipment_id,))
        cur.execute("DELETE FROM Maintenance_Schedule WHERE id = %s", (equipment_id,))
        conn.commit()
        flash('Equipment deleted successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete equipment: {str(e)}", "error")
    finally:
        if conn:
            conn.close()
    return redirect(url_for('maintenance'))

#Routines

@app.route('/add_exercise_to_routine', methods=['POST'])
def add_exercise_to_routine():
    member_id = session.get('user_id')
    if not member_id:
        return jsonify({'error': 'User not logged in'}), 403

    exercise_name = request.form['exercise_name']
    reps = request.form['reps']
    sets = request.form['sets']
    day_type = request.form['day_type']

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute("SELECT exercise_id FROM Exercises WHERE name = %s;", (exercise_name,))
        exercise = cur.fetchone()
        if exercise:
            exercise_id = exercise[0]
        else:
            cur.execute("INSERT INTO Exercises (name) VALUES (%s) RETURNING exercise_id;", (exercise_name,))
            exercise_id = cur.fetchone()[0]

        cur.execute("SELECT routine_id FROM Routines WHERE member_id = %s AND day_type = %s;", (member_id, day_type))
        routine = cur.fetchone()
        if routine:
            routine_id = routine[0]
        else:
            cur.execute("INSERT INTO Routines (member_id, day_type) VALUES (%s, %s) RETURNING routine_id;", (member_id, day_type))
            routine_id = cur.fetchone()[0]

        cur.execute("INSERT INTO Routine_Exercises (routine_id, exercise_id, reps, sets) VALUES (%s, %s, %s, %s);", (routine_id, exercise_id, reps, sets))
        conn.commit()
        return redirect(url_for('member_dashboard'))
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()






@app.route('/update_routine_exercise', methods=['POST'])
def update_routine_exercise():
    routine_exercise_id = request.form['routine_exercise_id']
    reps = request.form['reps']
    sets = request.form['sets']
    personal_record = request.form.get('personal_record', None)

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        update_query = """
            UPDATE Routine_Exercises
            SET reps = %s, sets = %s {}
            WHERE routine_exercise_id = %s
        """.format(", personal_record = %s" if personal_record else "")
        cur.execute(update_query, (reps, sets, personal_record, routine_exercise_id) if personal_record else (reps, sets, routine_exercise_id))
        conn.commit()
        flash("Exercise updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to update exercise: {str(e)}", "error")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return redirect(url_for('member_dashboard'))

@app.route('/delete_exercise_from_routine', methods=['POST'])
def delete_exercise_from_routine():
    routine_exercise_id = request.form['routine_exercise_id']

    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("DELETE FROM Routine_Exercises WHERE routine_exercise_id = %s", (routine_exercise_id,))
        conn.commit()
        flash("Exercise deleted from routine successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete exercise: {str(e)}", "error")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return redirect(url_for('member_dashboard'))

