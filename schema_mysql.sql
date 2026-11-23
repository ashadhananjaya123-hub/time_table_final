-- TimetablePro - MySQL Production Database Schema
-- Run this script in MySQL Workbench, phpMyAdmin, or mysql CLI:
-- mysql -u root -p < schema_mysql.sql

CREATE DATABASE IF NOT EXISTS timetablepro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE timetablepro;

-- 1. Departments
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 2. Users
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(30),
    department_id VARCHAR(50),
    roll_no VARCHAR(50),
    year INT,
    semester INT,
    section VARCHAR(10),
    created_at VARCHAR(50),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 3. Classrooms
CREATE TABLE IF NOT EXISTS classrooms (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'classroom',
    capacity INT NOT NULL DEFAULT 60,
    building VARCHAR(255)
) ENGINE=InnoDB;

-- 4. Subjects
CREATE TABLE IF NOT EXISTS subjects (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(30) NOT NULL,
    department_id VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    semester INT NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'theory',
    hours_per_week INT NOT NULL DEFAULT 4,
    teacher_id VARCHAR(50),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 5. Timetables
CREATE TABLE IF NOT EXISTS timetables (
    id VARCHAR(80) PRIMARY KEY,
    department_id VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    semester INT NOT NULL,
    section VARCHAR(10) DEFAULT 'A',
    published INT NOT NULL DEFAULT 0,
    generated_at VARCHAR(50),
    updated_at VARCHAR(50),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Timetable Slots
CREATE TABLE IF NOT EXISTS timetable_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timetable_id VARCHAR(80) NOT NULL,
    day VARCHAR(20) NOT NULL,
    period INT NOT NULL,
    subject_id VARCHAR(50),
    teacher_id VARCHAR(50),
    classroom_id VARCHAR(50),
    slot_type VARCHAR(30) NOT NULL DEFAULT 'regular',
    FOREIGN KEY (timetable_id) REFERENCES timetables(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE SET NULL,
    INDEX idx_slot_lookup (day, period, teacher_id, classroom_id)
) ENGINE=InnoDB;

-- 7. Mutual Swap Requests
CREATE TABLE IF NOT EXISTS swap_requests (
    id VARCHAR(50) PRIMARY KEY,
    sender_teacher_id VARCHAR(50) NOT NULL,
    receiver_teacher_id VARCHAR(50) NOT NULL,
    sender_day VARCHAR(20) NOT NULL,
    sender_period INT NOT NULL,
    sender_subject_id VARCHAR(50),
    receiver_day VARCHAR(20) NOT NULL,
    receiver_period INT NOT NULL,
    receiver_subject_id VARCHAR(50),
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    admin_notified INT NOT NULL DEFAULT 0,
    created_at VARCHAR(50),
    updated_at VARCHAR(50),
    FOREIGN KEY (sender_teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. Swap Audit History
CREATE TABLE IF NOT EXISTS swap_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    swap_request_id VARCHAR(50) NOT NULL,
    sender_name VARCHAR(255) NOT NULL,
    receiver_name VARCHAR(255) NOT NULL,
    details TEXT NOT NULL,
    executed_at VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

-- 9. Academic Events
CREATE TABLE IF NOT EXISTS academic_events (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(30) NOT NULL DEFAULT 'event',
    event_date VARCHAR(20) NOT NULL,
    start_time VARCHAR(10),
    end_time VARCHAR(10),
    affected_department_id VARCHAR(50),
    affected_year INT DEFAULT 0,
    affected_semester INT DEFAULT 0,
    periods_lost INT NOT NULL DEFAULT 0,
    created_at VARCHAR(50),
    FOREIGN KEY (affected_department_id) REFERENCES departments(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 10. Extra Classes (Lost Class Recovery)
CREATE TABLE IF NOT EXISTS extra_classes (
    id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50),
    subject_id VARCHAR(50) NOT NULL,
    teacher_id VARCHAR(50) NOT NULL,
    department_id VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    semester INT NOT NULL,
    replacement_date VARCHAR(20) NOT NULL,
    period INT NOT NULL,
    classroom_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    created_at VARCHAR(50),
    FOREIGN KEY (event_id) REFERENCES academic_events(id) ON DELETE SET NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 11. Activity Periods (Sports, Cultural, Music, Club)
CREATE TABLE IF NOT EXISTS activity_periods (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    activity_type VARCHAR(30) NOT NULL DEFAULT 'sports',
    day VARCHAR(20) NOT NULL,
    period INT NOT NULL,
    department_id VARCHAR(50),
    year INT DEFAULT 0,
    semester INT DEFAULT 0,
    coordinator_teacher_id VARCHAR(50),
    venue VARCHAR(255),
    created_at VARCHAR(50),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (coordinator_teacher_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 12. Syllabus Topics
CREATE TABLE IF NOT EXISTS syllabus_topics (
    id VARCHAR(50) PRIMARY KEY,
    subject_id VARCHAR(50) NOT NULL,
    teacher_id VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    chapter VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    completion_date VARCHAR(20),
    notes TEXT,
    created_at VARCHAR(50),
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 13. Assignments
CREATE TABLE IF NOT EXISTS assignments (
    id VARCHAR(50) PRIMARY KEY,
    subject_id VARCHAR(50) NOT NULL,
    teacher_id VARCHAR(50) NOT NULL,
    department_id VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    semester INT NOT NULL,
    section VARCHAR(10) DEFAULT 'A',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    issue_date VARCHAR(20) NOT NULL,
    due_date VARCHAR(20) NOT NULL,
    created_at VARCHAR(50),
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 14. Assignment Submissions
CREATE TABLE IF NOT EXISTS assignment_submissions (
    id VARCHAR(50) PRIMARY KEY,
    assignment_id VARCHAR(50) NOT NULL,
    student_id VARCHAR(50) NOT NULL,
    submission_date VARCHAR(30),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    grade VARCHAR(10),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 15. Announcements
CREATE TABLE IF NOT EXISTS announcements (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    target_department VARCHAR(50) DEFAULT 'all',
    target_year INT DEFAULT 0,
    target_semester INT DEFAULT 0,
    created_at VARCHAR(50)
) ENGINE=InnoDB;

-- 16. Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    user_role VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(255),
    is_read INT NOT NULL DEFAULT 0,
    created_at VARCHAR(50)
) ENGINE=InnoDB;
