"""
TimetablePro - Database Management & Abstraction Layer
Supports SQLite and MySQL with standardized dictionary queries, transactions,
schema initialization, and demonstration seeding.
"""

import sqlite3
import datetime
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    """
    Returns an active database connection and cursor supporting dictionary row access.
    """
    if Config.DB_TYPE == 'mysql':
        try:
            import pymysql
            import pymysql.cursors
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            return conn, 'mysql'
        except Exception as e:
            print(f"Warning: MySQL connection failed ({e}). Falling back to SQLite.")
    
    # Default to SQLite
    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn, 'sqlite'

def query_db(query, args=(), one=False, commit=False):
    """
    Execute queries and return dictionary results or lastrowid.
    """
    conn, db_type = get_db_connection()
    try:
        if db_type == 'sqlite':
            cur = conn.cursor()
            cur.execute(query, args)
            if commit:
                conn.commit()
                last_id = cur.lastrowid
                conn.close()
                return last_id
            rv = cur.fetchall()
            conn.close()
            # Convert sqlite3.Row to standard dict
            dicts = [dict(row) for row in rv]
            return (dicts[0] if dicts else None) if one else dicts
        else:
            with conn.cursor() as cur:
                cur.execute(query, args)
                if commit:
                    conn.commit()
                    last_id = cur.lastrowid
                    conn.close()
                    return last_id
                rv = cur.fetchall()
                conn.close()
                return (rv[0] if rv else None) if one else rv
    except Exception as e:
        if commit:
            conn.rollback()
        conn.close()
        raise e

def init_db():
    """
    Creates all application tables if they do not exist.
    """
    conn, db_type = get_db_connection()
    cur = conn.cursor()

    # Base table definitions
    id_pk = "INTEGER PRIMARY KEY AUTOINCREMENT" if db_type == 'sqlite' else "INT AUTO_INCREMENT PRIMARY KEY"
    text_type = "TEXT" if db_type == 'sqlite' else "VARCHAR(255)"
    long_text = "TEXT"

    statements = [
        f"""
        CREATE TABLE IF NOT EXISTS departments (
            id VARCHAR(50) PRIMARY KEY,
            name {text_type} NOT NULL,
            code VARCHAR(20) NOT NULL UNIQUE
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(50) PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash {text_type} NOT NULL,
            role VARCHAR(20) NOT NULL,
            name {text_type} NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(30),
            department_id VARCHAR(50),
            roll_no VARCHAR(50),
            year INT,
            semester INT,
            section VARCHAR(10),
            created_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS classrooms (
            id VARCHAR(50) PRIMARY KEY,
            name {text_type} NOT NULL,
            type VARCHAR(20) NOT NULL DEFAULT 'classroom',
            capacity INT NOT NULL DEFAULT 60,
            building {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS subjects (
            id VARCHAR(50) PRIMARY KEY,
            name {text_type} NOT NULL,
            code VARCHAR(30) NOT NULL,
            department_id VARCHAR(50) NOT NULL,
            year INT NOT NULL,
            semester INT NOT NULL,
            type VARCHAR(20) NOT NULL DEFAULT 'theory',
            hours_per_week INT NOT NULL DEFAULT 4,
            teacher_id VARCHAR(50)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS timetables (
            id VARCHAR(80) PRIMARY KEY,
            department_id VARCHAR(50) NOT NULL,
            year INT NOT NULL,
            semester INT NOT NULL,
            section VARCHAR(10) DEFAULT 'A',
            published INT NOT NULL DEFAULT 0,
            generated_at {text_type},
            updated_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS timetable_slots (
            id {id_pk},
            timetable_id VARCHAR(80) NOT NULL,
            day VARCHAR(20) NOT NULL,
            period INT NOT NULL,
            subject_id VARCHAR(50),
            teacher_id VARCHAR(50),
            classroom_id VARCHAR(50),
            slot_type VARCHAR(30) NOT NULL DEFAULT 'regular'
        )
        """,
        f"""
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
            reason {long_text} NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            admin_notified INT NOT NULL DEFAULT 0,
            created_at {text_type},
            updated_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS swap_history (
            id {id_pk},
            swap_request_id VARCHAR(50) NOT NULL,
            sender_name {text_type} NOT NULL,
            receiver_name {text_type} NOT NULL,
            details {long_text} NOT NULL,
            executed_at {text_type} NOT NULL
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS academic_events (
            id VARCHAR(50) PRIMARY KEY,
            title {text_type} NOT NULL,
            description {long_text},
            event_type VARCHAR(30) NOT NULL DEFAULT 'event',
            event_date VARCHAR(20) NOT NULL,
            start_time VARCHAR(10),
            end_time VARCHAR(10),
            affected_department_id VARCHAR(50),
            affected_year INT DEFAULT 0,
            affected_semester INT DEFAULT 0,
            periods_lost INT NOT NULL DEFAULT 0,
            created_at {text_type}
        )
        """,
        f"""
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
            created_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS activity_periods (
            id VARCHAR(50) PRIMARY KEY,
            name {text_type} NOT NULL,
            activity_type VARCHAR(30) NOT NULL DEFAULT 'sports',
            day VARCHAR(20) NOT NULL,
            period INT NOT NULL,
            department_id VARCHAR(50),
            year INT DEFAULT 0,
            semester INT DEFAULT 0,
            section VARCHAR(10) DEFAULT 'A',
            coordinator_teacher_id VARCHAR(50),
            venue {text_type},
            created_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS syllabus_topics (
            id VARCHAR(50) PRIMARY KEY,
            subject_id VARCHAR(50) NOT NULL,
            teacher_id VARCHAR(50) NOT NULL,
            title {text_type} NOT NULL,
            chapter {text_type},
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            completion_date VARCHAR(20),
            notes {long_text},
            created_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS assignments (
            id VARCHAR(50) PRIMARY KEY,
            subject_id VARCHAR(50) NOT NULL,
            teacher_id VARCHAR(50) NOT NULL,
            department_id VARCHAR(50) NOT NULL,
            year INT NOT NULL,
            semester INT NOT NULL,
            section VARCHAR(10) DEFAULT 'A',
            title {text_type} NOT NULL,
            description {long_text},
            issue_date VARCHAR(20) NOT NULL,
            due_date VARCHAR(20) NOT NULL,
            created_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id VARCHAR(50) PRIMARY KEY,
            assignment_id VARCHAR(50) NOT NULL,
            student_id VARCHAR(50) NOT NULL,
            submission_date VARCHAR(30),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            notes {long_text},
            grade VARCHAR(10)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS announcements (
            id VARCHAR(50) PRIMARY KEY,
            title {text_type} NOT NULL,
            content {long_text} NOT NULL,
            target_department VARCHAR(50) DEFAULT 'all',
            target_year INT DEFAULT 0,
            target_semester INT DEFAULT 0,
            created_at {text_type}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS notifications (
            id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            user_role VARCHAR(20),
            title {text_type} NOT NULL,
            message {long_text} NOT NULL,
            link {text_type},
            is_read INT NOT NULL DEFAULT 0,
            created_at {text_type}
        )
        """
    ]

    for stmt in statements:
        cur.execute(stmt)

    conn.commit()
    conn.close()

def seed_initial_data():
    """
    Seeds comprehensive initial records for demonstration:
    Departments, Teachers, Students, Classrooms, Subjects, Timetables,
    Syllabus, Assignments, Events, Activity Periods, and Notifications.
    """
    # Check if data already exists
    existing_user = query_db("SELECT id FROM users LIMIT 1", one=True)
    if existing_user:
        return

    now = datetime.datetime.now().isoformat()

    # 1. Departments
    departments = [
        ('dept_1', 'Computer Science and Engineering', 'CSE'),
        ('dept_2', 'Electronics and Communication Engineering', 'ECE'),
        ('dept_3', 'Mechanical Engineering', 'ME')
    ]
    for d in departments:
        query_db("INSERT INTO departments (id, name, code) VALUES (?, ?, ?)", d, commit=True)

    # 2. Classrooms & Labs
    classrooms = [
        ('cls_1', 'Room 101', 'classroom', 60, 'Main Academic Block'),
        ('cls_2', 'Room 102', 'classroom', 60, 'Main Academic Block'),
        ('cls_3', 'Room 201', 'classroom', 60, 'Science Block'),
        ('cls_4', 'Room 202', 'classroom', 60, 'Science Block'),
        ('cls_5', 'Room 301', 'classroom', 45, 'Main Academic Block'),
        ('cls_6', 'CS Computing Lab 1', 'lab', 40, 'Advanced Technology Center'),
        ('cls_7', 'CS Computing Lab 2', 'lab', 40, 'Advanced Technology Center'),
        ('cls_8', 'ECE Hardware Lab 1', 'lab', 35, 'Electronics Wing'),
        ('cls_9', 'Mechanical Workshop', 'lab', 30, 'Mechanical Hangar'),
        ('cls_10', 'Room 103', 'classroom', 60, 'Main Academic Block')
    ]
    for c in classrooms:
        query_db("INSERT INTO classrooms (id, name, type, capacity, building) VALUES (?, ?, ?, ?, ?)", c, commit=True)

    # 3. Administrator User
    admin_hash = generate_password_hash('admin123')
    query_db(
        "INSERT INTO users (id, username, password_hash, role, name, email, phone, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('adm_1', 'admin', admin_hash, 'admin', 'System Administrator', 'admin@college.edu', '9800000000', now),
        commit=True
    )

    # 4. Teachers (12 Faculty Members)
    tch_pass = generate_password_hash('teacher123')
    teachers = [
        ('tch_1', 'rajesh', tch_pass, 'teacher', 'Dr. Rajesh Kumar', 'rajesh@college.edu', '9876543210', 'dept_1', now),
        ('tch_2', 'sneha', tch_pass, 'teacher', 'Prof. Sneha Iyer', 'sneha@college.edu', '9876543211', 'dept_1', now),
        ('tch_3', 'anil', tch_pass, 'teacher', 'Dr. Anil Mehta', 'anil@college.edu', '9876543212', 'dept_1', now),
        ('tch_4', 'priya', tch_pass, 'teacher', 'Prof. Priya Nair', 'priya@college.edu', '9876543213', 'dept_1', now),
        ('tch_5', 'vikram', tch_pass, 'teacher', 'Dr. Vikram Singh', 'vikram@college.edu', '9876543214', 'dept_2', now),
        ('tch_6', 'kavitha', tch_pass, 'teacher', 'Prof. Kavitha Rao', 'kavitha@college.edu', '9876543215', 'dept_2', now),
        ('tch_7', 'suresh', tch_pass, 'teacher', 'Dr. Suresh Babu', 'suresh@college.edu', '9876543216', 'dept_2', now),
        ('tch_8', 'meena', tch_pass, 'teacher', 'Prof. Meena Devi', 'meena@college.edu', '9876543217', 'dept_2', now),
        ('tch_9', 'prakash', tch_pass, 'teacher', 'Dr. Prakash Joshi', 'prakash@college.edu', '9876543218', 'dept_3', now),
        ('tch_10', 'lakshmi', tch_pass, 'teacher', 'Prof. Lakshmi Menon', 'lakshmi@college.edu', '9876543219', 'dept_3', now),
        ('tch_11', 'ramesh', tch_pass, 'teacher', 'Dr. Ramesh Gupta', 'ramesh@college.edu', '9876543220', 'dept_3', now),
        ('tch_12', 'anitha', tch_pass, 'teacher', 'Prof. Anitha Krishnan', 'anitha@college.edu', '9876543221', 'dept_3', now)
    ]
    for t in teachers:
        query_db(
            "INSERT INTO users (id, username, password_hash, role, name, email, phone, department_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            t, commit=True
        )

    # 5. Students
    stu_pass = generate_password_hash('student123')
    students = [
        ('stu_1', 'amit', stu_pass, 'student', 'Amit Sharma', 'amit@college.edu', '9123456780', 'dept_1', 'CSE2024001', 1, 1, 'A', now),
        ('stu_2', 'priyap', stu_pass, 'student', 'Priya Patel', 'priyap@college.edu', '9123456781', 'dept_1', 'CSE2024002', 1, 1, 'A', now),
        ('stu_3', 'rahul', stu_pass, 'student', 'Rahul Verma', 'rahul@college.edu', '9123456782', 'dept_1', 'CSE2024003', 1, 2, 'A', now),
        ('stu_4', 'deepa', stu_pass, 'student', 'Deepa Menon', 'deepa@college.edu', '9123456783', 'dept_2', 'ECE2023001', 2, 3, 'A', now),
        ('stu_5', 'karthik', stu_pass, 'student', 'Karthik Reddy', 'karthik@college.edu', '9123456784', 'dept_3', 'ME2024001', 1, 1, 'A', now)
    ]
    for s in students:
        query_db(
            "INSERT INTO users (id, username, password_hash, role, name, email, phone, department_id, roll_no, year, semester, section, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            s, commit=True
        )

    # 6. Subjects (6 subjects per representative cohort)
    subjects = [
        # CSE Year 1 Semester 1
        ('sub_1', 'Data Structures', 'CS201', 'dept_1', 1, 1, 'theory', 4, 'tch_1'),
        ('sub_2', 'Digital Logic Design', 'CS202', 'dept_1', 1, 1, 'theory', 4, 'tch_2'),
        ('sub_3', 'Mathematics I', 'MA101', 'dept_1', 1, 1, 'theory', 4, 'tch_3'),
        ('sub_4', 'English Communication', 'EN101', 'dept_1', 1, 1, 'theory', 3, 'tch_4'),
        ('sub_5', 'Programming Laboratory', 'CS291', 'dept_1', 1, 1, 'lab', 4, 'tch_1'),
        ('sub_6', 'Digital Electronics Lab', 'CS292', 'dept_1', 1, 1, 'lab', 2, 'tch_2'),

        # CSE Year 1 Semester 2
        ('sub_7', 'Object Oriented Programming', 'CS203', 'dept_1', 1, 2, 'theory', 4, 'tch_1'),
        ('sub_8', 'Computer Organization', 'CS204', 'dept_1', 1, 2, 'theory', 4, 'tch_2'),
        ('sub_9', 'Mathematics II', 'MA102', 'dept_1', 1, 2, 'theory', 4, 'tch_3'),
        ('sub_10', 'Environmental Studies', 'ES101', 'dept_1', 1, 2, 'theory', 3, 'tch_4'),
        ('sub_11', 'OOP Java Laboratory', 'CS293', 'dept_1', 1, 2, 'lab', 4, 'tch_1'),
        ('sub_12', 'Hardware Simulation Lab', 'CS294', 'dept_1', 1, 2, 'lab', 2, 'tch_2'),

        # ECE Year 2 Semester 3
        ('sub_13', 'Signals and Systems', 'EC301', 'dept_2', 2, 3, 'theory', 4, 'tch_5'),
        ('sub_14', 'Analog Circuits', 'EC302', 'dept_2', 2, 3, 'theory', 4, 'tch_6'),
        ('sub_15', 'Electromagnetic Theory', 'EC303', 'dept_2', 2, 3, 'theory', 4, 'tch_7'),
        ('sub_16', 'Probability and Statistics', 'MA201', 'dept_2', 2, 3, 'theory', 3, 'tch_8'),
        ('sub_17', 'Analog Circuits Lab', 'EC391', 'dept_2', 2, 3, 'lab', 4, 'tch_6'),
        ('sub_18', 'Signals Processing Lab', 'EC392', 'dept_2', 2, 3, 'lab', 2, 'tch_5'),

        # ME Year 1 Semester 1
        ('sub_19', 'Engineering Mechanics', 'ME101', 'dept_3', 1, 1, 'theory', 4, 'tch_9'),
        ('sub_20', 'Engineering Drawing', 'ME102', 'dept_3', 1, 1, 'theory', 4, 'tch_10'),
        ('sub_21', 'Thermodynamics', 'ME103', 'dept_3', 1, 1, 'theory', 4, 'tch_11'),
        ('sub_22', 'Applied Physics', 'PH101', 'dept_3', 1, 1, 'theory', 3, 'tch_12'),
        ('sub_23', 'Mechanical Workshop Lab', 'ME191', 'dept_3', 1, 1, 'lab', 4, 'tch_9'),
        ('sub_24', 'Applied Physics Lab', 'PH191', 'dept_3', 1, 1, 'lab', 2, 'tch_12')
    ]
    for sub in subjects:
        query_db(
            "INSERT INTO subjects (id, name, code, department_id, year, semester, type, hours_per_week, teacher_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sub, commit=True
        )

    # 7. Published Master Timetable for CSE Year 1 Semester 1
    tt_id = 'tt_dept_1_1_1'
    query_db(
        "INSERT INTO timetables (id, department_id, year, semester, section, published, generated_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (tt_id, 'dept_1', 1, 1, 'A', 1, now, now), commit=True
    )

    slots = [
        # Monday
        (tt_id, 'Monday', 1, 'sub_1', 'tch_1', 'cls_1', 'regular'),
        (tt_id, 'Monday', 2, 'sub_2', 'tch_2', 'cls_2', 'regular'),
        (tt_id, 'Monday', 3, 'sub_3', 'tch_3', 'cls_1', 'regular'),
        (tt_id, 'Monday', 6, 'sub_5', 'tch_1', 'cls_6', 'lab'),
        (tt_id, 'Monday', 7, 'sub_5', 'tch_1', 'cls_6', 'lab'),

        # Tuesday
        (tt_id, 'Tuesday', 1, 'sub_2', 'tch_2', 'cls_2', 'regular'),
        (tt_id, 'Tuesday', 2, 'sub_1', 'tch_1', 'cls_1', 'regular'),
        (tt_id, 'Tuesday', 3, 'sub_4', 'tch_4', 'cls_3', 'regular'),
        (tt_id, 'Tuesday', 6, 'sub_6', 'tch_2', 'cls_7', 'lab'),
        (tt_id, 'Tuesday', 7, 'sub_6', 'tch_2', 'cls_7', 'lab'),

        # Wednesday
        (tt_id, 'Wednesday', 1, 'sub_1', 'tch_1', 'cls_1', 'regular'),
        (tt_id, 'Wednesday', 2, 'sub_3', 'tch_3', 'cls_1', 'regular'),
        (tt_id, 'Wednesday', 3, 'sub_2', 'tch_2', 'cls_2', 'regular'),
        (tt_id, 'Wednesday', 8, None, 'tch_4', 'cls_1', 'activity'), # Sports Activity

        # Thursday
        (tt_id, 'Thursday', 1, 'sub_3', 'tch_3', 'cls_1', 'regular'),
        (tt_id, 'Thursday', 2, 'sub_1', 'tch_1', 'cls_1', 'regular'),
        (tt_id, 'Thursday', 3, 'sub_4', 'tch_4', 'cls_3', 'regular'),
        (tt_id, 'Thursday', 6, 'sub_5', 'tch_1', 'cls_6', 'lab'),
        (tt_id, 'Thursday', 7, 'sub_5', 'tch_1', 'cls_6', 'lab'),

        # Friday
        (tt_id, 'Friday', 1, 'sub_2', 'tch_2', 'cls_2', 'regular'),
        (tt_id, 'Friday', 2, 'sub_4', 'tch_4', 'cls_3', 'regular'),

        # Saturday
        (tt_id, 'Saturday', 1, 'sub_3', 'tch_3', 'cls_1', 'regular')
    ]
    for s in slots:
        query_db(
            "INSERT INTO timetable_slots (timetable_id, day, period, subject_id, teacher_id, classroom_id, slot_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            s, commit=True
        )

    # 8. Activity Periods
    query_db(
        "INSERT INTO activity_periods (id, name, activity_type, day, period, department_id, year, semester, section, coordinator_teacher_id, venue, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('act_1', 'Inter-House Sports & Fitness', 'sports', 'Wednesday', 8, 'dept_1', 1, 1, 'A', 'tch_4', 'College Sports Ground', now),
        commit=True
    )
    query_db(
        "INSERT INTO activity_periods (id, name, activity_type, day, period, department_id, year, semester, section, coordinator_teacher_id, venue, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('act_2', 'Coding Club & Innovation Hub', 'club', 'Friday', 7, 'dept_1', 1, 1, 'A', 'tch_1', 'CS Computing Lab 1', now),
        commit=True
    )

    # 9. Academic Events & Lost Class Recovery Demo
    query_db(
        "INSERT INTO academic_events (id, title, description, event_type, event_date, start_time, end_time, affected_department_id, affected_year, affected_semester, periods_lost, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('ev_1', 'Annual Science and Tech Symposium', 'Keynote address by industry experts and student technical exhibitions.', 'seminar', '2026-11-20', '09:00', '13:00', 'dept_1', 1, 1, 3, now),
        commit=True
    )
    # Extra class allocated to recover one of the lost periods
    query_db(
        "INSERT INTO extra_classes (id, event_id, subject_id, teacher_id, department_id, year, semester, replacement_date, period, classroom_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('ext_1', 'ev_1', 'sub_1', 'tch_1', 'dept_1', 1, 1, '2026-11-22', 4, 'cls_1', 'scheduled', now),
        commit=True
    )

    # 10. Syllabus Progress Topics
    syllabus = [
        ('syl_1', 'sub_1', 'tch_1', 'Arrays and Multi-dimensional Matrices', 'Chapter 1', 'completed', '2026-10-15', 'Covered row/col major indexing and applications.', now),
        ('syl_2', 'sub_1', 'tch_1', 'Singly and Doubly Linked Lists', 'Chapter 2', 'completed', '2026-10-28', 'Addressed pointer mechanics and circular structures.', now),
        ('syl_3', 'sub_1', 'tch_1', 'Stack Applications & Infix-to-Postfix', 'Chapter 3', 'completed', '2026-11-05', 'Demonstrated parenthesis balancing algorithms.', now),
        ('syl_4', 'sub_1', 'tch_1', 'Queues and Priority Heaps', 'Chapter 4', 'pending', None, 'Scheduled for week 8.', now),
        ('syl_5', 'sub_1', 'tch_1', 'Binary Search Trees & AVL Balancing', 'Chapter 5', 'pending', None, 'Advanced tree traversals.', now),
        ('syl_6', 'sub_1', 'tch_1', 'Graph Representation & Dijkstra Algorithm', 'Chapter 6', 'pending', None, 'Final syllabus module.', now),

        ('syl_7', 'sub_2', 'tch_2', 'Boolean Algebra & De Morgans Laws', 'Chapter 1', 'completed', '2026-10-12', 'Covered canonical SOP and POS forms.', now),
        ('syl_8', 'sub_2', 'tch_2', 'Karnaugh Maps 3 and 4 Variables', 'Chapter 2', 'completed', '2026-10-25', 'Practiced don\'t care conditions.', now),
        ('syl_9', 'sub_2', 'tch_2', 'Combinational Logic: Adders & Multiplexers', 'Chapter 3', 'pending', None, 'In progress.', now)
    ]
    for s in syllabus:
        query_db(
            "INSERT INTO syllabus_topics (id, subject_id, teacher_id, title, chapter, status, completion_date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            s, commit=True
        )

    # 11. Assignments & Submissions
    query_db(
        "INSERT INTO assignments (id, subject_id, teacher_id, department_id, year, semester, section, title, description, issue_date, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('asn_1', 'sub_1', 'tch_1', 'dept_1', 1, 1, 'A', 'Assignment 1: Linked List Inversion & Cycle Detection', 'Implement cycle detection using Floyd Tortoise and Hare algorithm. Submit C++ or Java code with edge case analysis.', '2026-11-01', '2026-11-20', now),
        commit=True
    )
    query_db(
        "INSERT INTO assignments (id, subject_id, teacher_id, department_id, year, semester, section, title, description, issue_date, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('asn_2', 'sub_2', 'tch_2', 'dept_1', 1, 1, 'A', 'Assignment 1: 4-Bit ALU Schematic Design', 'Design an Arithmetic Logic Unit carrying out addition, subtraction, AND, and OR operations using Logisim.', '2026-11-05', '2026-11-25', now),
        commit=True
    )

    # Submissions
    query_db(
        "INSERT INTO assignment_submissions (id, assignment_id, student_id, submission_date, status, notes, grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('subm_1', 'asn_1', 'stu_1', '2026-11-10', 'submitted', 'Code verified with unit tests.', 'A+'),
        commit=True
    )
    query_db(
        "INSERT INTO assignment_submissions (id, assignment_id, student_id, submission_date, status, notes, grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('subm_2', 'asn_1', 'stu_2', None, 'pending', 'Working on edge cases.', None),
        commit=True
    )

    # 12. Mutual Teacher Swap Request Demo
    query_db(
        "INSERT INTO swap_requests (id, sender_teacher_id, receiver_teacher_id, sender_day, sender_period, sender_subject_id, receiver_day, receiver_period, receiver_subject_id, reason, status, admin_notified, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('swap_demo_1', 'tch_1', 'tch_2', 'Monday', 1, 'sub_1', 'Tuesday', 1, 'sub_2', 'Faculty research committee review meeting scheduled Monday 9:00 AM.', 'pending', 0, now, now),
        commit=True
    )

    # 13. Announcements
    query_db(
        "INSERT INTO announcements (id, title, content, target_department, target_year, target_semester, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('ann_1', 'Welcome to Academic Year 2026-2027', 'All academic sessions will proceed according to the published timetable. Students are expected to maintain at least 75% attendance across all subjects.', 'all', 0, 0, now),
        commit=True
    )
    query_db(
        "INSERT INTO announcements (id, title, content, target_department, target_year, target_semester, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('ann_2', 'CSE Laboratory Protocol & Safety Standards', 'All first year CSE students must carry their laboratory journals and college ID cards during practical laboratory periods.', 'dept_1', 1, 1, now),
        commit=True
    )

    # 14. Notifications
    query_db(
        "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('notif_1', 'tch_2', 'teacher', 'New Mutual Class Swap Request', 'Dr. Rajesh Kumar requested a class swap: Monday Period 1 (Data Structures) for your Tuesday Period 1 (Digital Logic).', '/teacher#swaps', 0, now),
        commit=True
    )
    query_db(
        "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('notif_2', 'stu_1', 'student', 'Official Timetable Published', 'The official class timetable for CSE Year 1 Semester 1 has been published.', '/student#timetable', 0, now),
        commit=True
    )
    query_db(
        "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ('notif_3', 'adm_1', 'admin', 'System Initialized', 'TimetablePro database schema and academic records initialized successfully.', '/admin', 0, now),
        commit=True
    )

    # 15. Seed SJBIT CSE Faculty and Master Schedules
    try:
        import seed_sjbit_data
        seed_sjbit_data.run_seed()
    except Exception as e:
        print(f"SJBIT faculty seeding notice: {e}")
