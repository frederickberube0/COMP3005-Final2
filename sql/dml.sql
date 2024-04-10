-- Insert Users for Admins
INSERT INTO Users (email, password, role, picture_link) VALUES 
('fred@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Admin', 'profile_pictures/male/1.jpg'),
('julian@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Admin', 'profile_pictures/male/3.jpg')
RETURNING id;

-- Insert Admins using the returned IDs from above (use the actual IDs returned by the previous INSERT command)
INSERT INTO Admin (id, name) VALUES 
((SELECT id FROM Users WHERE email='fred@gmail.com'), 'Fred'),
((SELECT id FROM Users WHERE email='julian@gmail.com'), 'Julian');

-- Insert Users for Trainers
INSERT INTO Users (email, password, role, picture_link) VALUES 
('alice@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Trainer', 'profile_pictures/female/2.jpg'),
('bob@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Trainer', 'profile_pictures/male/7.jpg')
RETURNING id;

-- Insert Trainers using the returned IDs
INSERT INTO Trainers (id, name, specialization) VALUES 
((SELECT id FROM Users WHERE email='alice@gmail.com'), 'Alice', 'Cardio'),
((SELECT id FROM Users WHERE email='bob@gmail.com'), 'Bob', 'Strength training');

-- Insert Users for Members and Members themselves with Health Metrics
WITH member_users AS (
    INSERT INTO Users (email, password, role, picture_link) VALUES 
    ('john.doe@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Member', 'profile_pictures/male/8.jpg'),
    ('jane.smith@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Member', 'profile_pictures/female/4.jpg'),
    ('emily.davis@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Member', 'profile_pictures/female/5.jpg'),
    ('michael.brown@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Member', 'profile_pictures/male/9.jpg'),
    ('chloe.johnson@gmail.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Member', 'profile_pictures/female/6.jpg')
    RETURNING id
),
member_details AS (
    INSERT INTO Members (id, name, age, gender, preferred_trainer_id) SELECT id, 
    CASE 
        WHEN id=(SELECT id FROM member_users LIMIT 1) THEN 'John Doe' 
        WHEN id=(SELECT id FROM member_users OFFSET 1 LIMIT 1) THEN 'Jane Smith' 
        WHEN id=(SELECT id FROM member_users OFFSET 2 LIMIT 1) THEN 'Emily Davis' 
        WHEN id=(SELECT id FROM member_users OFFSET 3 LIMIT 1) THEN 'Michael Brown' 
        WHEN id=(SELECT id FROM member_users OFFSET 4 LIMIT 1) THEN 'Chloe Johnson' 
    END,
    CASE 
        WHEN id=(SELECT id FROM member_users LIMIT 1) THEN 25 
        WHEN id=(SELECT id FROM member_users OFFSET 1 LIMIT 1) THEN 30 
        WHEN id=(SELECT id FROM member_users OFFSET 2 LIMIT 1) THEN 22 
        WHEN id=(SELECT id FROM member_users OFFSET 3 LIMIT 1) THEN 28 
        WHEN id=(SELECT id FROM member_users OFFSET 4 LIMIT 1) THEN 32 
    END,
    CASE 
        WHEN id=(SELECT id FROM member_users LIMIT 1) THEN 'Male' 
        WHEN id=(SELECT id FROM member_users OFFSET 1 LIMIT 1) THEN 'Female' 
        WHEN id=(SELECT id FROM member_users OFFSET 2 LIMIT 1) THEN 'Female' 
        WHEN id=(SELECT id FROM member_users OFFSET 3 LIMIT 1) THEN 'Male' 
        WHEN id=(SELECT id FROM member_users OFFSET 4 LIMIT 1) THEN 'Female' 
    END,
    (SELECT id FROM Trainers LIMIT 1)
    FROM member_users
    RETURNING id
)
INSERT INTO Health_Metrics (member_id, height, desired_weight, weight, endurance_importance, strength_importance) SELECT id, 
CASE 
    WHEN id=(SELECT id FROM member_details LIMIT 1) THEN 170.5 
    WHEN id=(SELECT id FROM member_details OFFSET 1 LIMIT 1) THEN 165.3 
    WHEN id=(SELECT id FROM member_details OFFSET 2 LIMIT 1) THEN 175.0 
    WHEN id=(SELECT id FROM member_details OFFSET 3 LIMIT 1) THEN 180.2 
    WHEN id=(SELECT id FROM member_details OFFSET 4 LIMIT 1) THEN 160.0 
END,

    CASE 
        WHEN id=(SELECT id FROM member_users LIMIT 1) THEN 100
        WHEN id=(SELECT id FROM member_users OFFSET 1 LIMIT 1) THEN 100
        WHEN id=(SELECT id FROM member_users OFFSET 2 LIMIT 1) THEN 100
        WHEN id=(SELECT id FROM member_users OFFSET 3 LIMIT 1) THEN 100
        WHEN id=(SELECT id FROM member_users OFFSET 4 LIMIT 1) THEN 100
    END,
CASE 
    WHEN id=(SELECT id FROM member_details LIMIT 1) THEN 70 
    WHEN id=(SELECT id FROM member_details OFFSET 1 LIMIT 1) THEN 60 
    WHEN id=(SELECT id FROM member_details OFFSET 2 LIMIT 1) THEN 65 
    WHEN id=(SELECT id FROM member_details OFFSET 3 LIMIT 1) THEN 80 
    WHEN id=(SELECT id FROM member_details OFFSET 4 LIMIT 1) THEN 55 
END,
3,
4
FROM member_details;

-- Insert Rooms
INSERT INTO Room (number, capacity) 
VALUES 
(101, 30),
(102, 30),
(103, 30),
(104, 30),
(105, 30),
(106, 30),
(107, 30),
(108, 30),
(109, 30),
(110, 30);

-- Insert Equipment
INSERT INTO Equipment (equipment_name) VALUES 
('Treadmill'), 
('Elliptical'), 
('Stationary Bike'), 
('Dumbbell Set'), 
('Barbell Set');

INSERT INTO Maintenance_Schedule (id, day_of_week, time, frequency) VALUES 
(1, 'Monday', '10:00', 'Weekly'),
(2, 'Tuesday', '10:00', 'Weekly'),
(3, 'Wednesday', '10:00', 'Weekly'),
(4, 'Thursday', '10:00', 'Weekly'),
(5, 'Friday', '10:00', 'Weekly');

INSERT INTO Trainer_Availiblity (id, day_of_week, start_time, end_time) VALUES
(3, 'Monday', '09:00', '17:00'),
(3, 'Tuesday', '09:00', '17:00'),
(3, 'Wednesday', '09:00', '17:00'),
(3, 'Thursday', '09:00', '17:00'),
(3, 'Friday', '09:00', '17:00'),
(4, 'Monday', '09:00', '17:00'),
(4, 'Tuesday', '09:00', '17:00'),
(4, 'Wednesday', '09:00', '17:00'),
(4, 'Thursday', '09:00', '17:00'),
(4, 'Friday', '09:00', '17:00');
