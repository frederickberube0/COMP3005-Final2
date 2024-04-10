-- Users Table
CREATE TABLE Users (
    email VARCHAR(255) PRIMARY KEY,
    id SERIAL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    picture_link VARCHAR(255)
);

-- Trainers Table
CREATE TABLE Trainers (
    id INT PRIMARY KEY REFERENCES Users(id),
    name VARCHAR(255) NOT NULL,
    specialization TEXT
);

-- Members Table
CREATE TABLE Members (
    id INT PRIMARY KEY REFERENCES Users(id),
    name VARCHAR(255) NOT NULL,
    age INT,
    gender VARCHAR(50),
    preferred_trainer_id INT REFERENCES Trainers(id)
);


CREATE TABLE Trainer_Availiblity (
    id INT REFERENCES Trainers(id),
    day_of_week VARCHAR(10) CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    PRIMARY KEY (id, day_of_week)
);

-- Admin Table
CREATE TABLE Admin (
    id INT PRIMARY KEY REFERENCES Users(id),
    name VARCHAR(255) NOT NULL
);

-- Health Metrics Table
CREATE TABLE Health_Metrics (
    member_id INT PRIMARY KEY REFERENCES Members(id),
    height DECIMAL,
    weight DECIMAL,
    desired_weight DECIMAL,
    endurance_importance INT,
    strength_importance INT
);

-- Equipment Table
CREATE TABLE Equipment (
    equipment_id SERIAL PRIMARY KEY,
    equipment_name VARCHAR(255) NOT NULL
);

CREATE TABLE Maintenance_Schedule (
    id INT,
    day_of_week VARCHAR(10) CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    time TIME,
    frequency VARCHAR(10) CHECK (frequency IN ('Daily', 'Weekly', 'Bi-Weekly', 'Monthly', 'Yearly')),
    PRIMARY KEY (id, day_of_week)
);

-- Room Table
CREATE TABLE Room (
    id SERIAL PRIMARY KEY,
    number INT,
    capacity INT
);

CREATE TABLE Room_Availability (
    id SERIAL PRIMARY KEY,
    room_id INT REFERENCES Room(id),
    day_of_week VARCHAR(10) CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL
);


-- Event Table
CREATE TABLE Event (
    event_id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    staff_id INT REFERENCES Trainers(id),
    room_id INT REFERENCES Room(id),
    time TIME,
    day_of_week VARCHAR(10) CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    type VARCHAR(10) CHECK (type IN ('Group', 'Individual'))
);

-- Attendees Table
CREATE TABLE Attendees (
    attendee_id INT REFERENCES Members(id),
    event_id INT REFERENCES Event(event_id),
    PRIMARY KEY (attendee_id, event_id)
);

-- Payments Table
CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    member_id INT REFERENCES Members(id),
    event_id INT REFERENCES Event(event_id),
    time_of_purchase TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_paid DECIMAL(10, 2),
    credit_card_number VARCHAR(16)
);


CREATE TABLE Routines (
    routine_id SERIAL PRIMARY KEY,
    member_id INT REFERENCES Members(id),
    day_type VARCHAR(8) CHECK (day_type IN ('Push Day', 'Pull Day', 'Leg Day')) 
);

CREATE TABLE Exercises (
    exercise_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE Routine_Exercises (
    routine_exercise_id SERIAL PRIMARY KEY,
    routine_id INT REFERENCES Routines(routine_id),
    exercise_id INT REFERENCES Exercises(exercise_id),
    reps INT,
    sets INT,
    personal_record DECIMAL
);