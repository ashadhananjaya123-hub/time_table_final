"""
TimetablePro - Core Flask Web Application & API Controller
Provides secure session management, role-based decorators,
Bento dashboard views, and RESTful API endpoints for:
- Administration, Faculty, and Student workspaces
- Timetable generation & interactive slot editing
- Mutual teacher-to-teacher class swapping
- Faculty utilization analytics & Chart.js payloads
- FullCalendar feeds (Day/Week/Month)
- Syllabus & Assignment tracking
- Events, workshops & lost-class recovery
- Sports & cultural activity periods
- Real-time notifications
"""

import os
import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database import init_db, seed_initial_data, query_db
from scheduler import generate_timetable, validate_timetable_slots, get_periods_config, get_days_config
from swap_manager import create_swap_request, process_swap_decision
from analytics import get_faculty_workload_analytics

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database tables and initial demonstration data exist
with app.app_context():
    init_db()
    seed_initial_data()

# ==============================================================================
# Security & Role-Based Access Control Decorators
# ==============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401
                return redirect('/login')
            if session.get('role') not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Forbidden", "message": "Access denied for current user role."}), 403
                # Redirect to appropriate user dashboard
                role = session.get('role')
                if role == 'admin':
                    return redirect('/admin')
                elif role == 'teacher':
                    return redirect('/teacher')
                elif role == 'student':
                    return redirect('/student')
                return redirect('/login')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    if 'user_id' not in session:
        return None
    return query_db(
        "SELECT id, username, role, name, email, phone, department_id, roll_no, year, semester, section FROM users WHERE id = ?",
        (session['user_id'],),
        one=True
    )

# ==============================================================================
# HTML Template Route Controllers
# ==============================================================================

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect('/admin')
        elif role == 'teacher':
            return redirect('/teacher')
        elif role == 'student':
            return redirect('/student')
    return redirect('/login')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/admin')
@role_required(['admin'])
def admin_dashboard():
    user = get_current_user()
    return render_template('admin.html', user=user)

@app.route('/teacher')
@role_required(['teacher'])
def teacher_dashboard():
    user = get_current_user()
    return render_template('teacher.html', user=user)

@app.route('/student')
@role_required(['student'])
def student_dashboard():
    user = get_current_user()
    return render_template('student.html', user=user)

# ==============================================================================
# Authentication APIs
# ==============================================================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip().lower()
    password = data.get('password') or ''
    role = (data.get('role') or '').strip().lower()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    # Locate user by unique username
    user = query_db(
        "SELECT * FROM users WHERE LOWER(username) = ?",
        (username,),
        one=True
    )

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['name'] = user['name']
    session.permanent = True

    redirect_url = f"/{user['role']}"
    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['name']}.",
        "redirect_url": redirect_url,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "name": user['name'],
            "role": user['role']
        }
    })

@app.route('/api/auth/logout', methods=['POST', 'GET'])
def api_logout():
    session.clear()
    if request.is_json:
        return jsonify({"success": True, "message": "Session terminated."})
    return redirect('/login')

@app.route('/api/auth/me', methods=['GET'])
@login_required
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"success": True, "user": user})

# In-memory store for verification codes: {username: {"otp": "...", "expires_at": ...}}
PASSWORD_RESET_OTPS = {}

@app.route('/api/auth/forgot-password/request-otp', methods=['POST'])
def api_forgot_password_request_otp():
    import random
    data = request.get_json() or {}
    username = (data.get('username') or '').strip().lower()
    email = (data.get('email') or '').strip().lower()
    phone = (data.get('phone') or '').strip().replace(' ', '').replace('-', '')

    if not username or not email or not phone:
        return jsonify({"success": False, "message": "Username, registered email, and mobile number are required."}), 400

    user = query_db(
        "SELECT id, username, name, email, phone FROM users WHERE LOWER(username) = ?",
        (username,),
        one=True
    )
    if not user:
        return jsonify({"success": False, "message": "No account found matching this username."}), 404

    # Verify email and mobile number match records
    user_email = (user.get('email') or '').strip().lower()
    user_phone = (user.get('phone') or '').strip().replace(' ', '').replace('-', '')

    if not user_email or user_email != email:
        return jsonify({"success": False, "message": "Email address does not match institutional records for this account."}), 400

    if not user_phone or user_phone != phone:
        return jsonify({"success": False, "message": "Mobile number does not match institutional records for this account."}), 400

    # Generate 6-digit verification code (valid for 10 minutes)
    otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.datetime.now().timestamp() + 600

    PASSWORD_RESET_OTPS[username] = {
        "otp": otp,
        "expires_at": expires_at,
        "email": email,
        "phone": phone
    }

    # Mask email and phone for user feedback
    masked_email = email[:3] + "***@" + email.split('@')[-1] if '@' in email else email
    masked_phone = "******" + phone[-4:] if len(phone) >= 4 else phone

    return jsonify({
        "success": True,
        "message": f"Verification code sent to {masked_email} and {masked_phone}.",
        "demo_otp": otp
    })

@app.route('/api/auth/forgot-password/verify-and-reset', methods=['POST'])
def api_forgot_password_verify_and_reset():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip().lower()
    otp = (data.get('otp') or '').strip()
    new_password = (data.get('new_password') or '').strip()

    if not username or not otp or not new_password:
        return jsonify({"success": False, "message": "Username, verification code, and new password are required."}), 400

    if len(new_password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400

    record = PASSWORD_RESET_OTPS.get(username)
    if not record:
        return jsonify({"success": False, "message": "No active verification request found. Please request a new code."}), 400

    if datetime.datetime.now().timestamp() > record['expires_at']:
        del PASSWORD_RESET_OTPS[username]
        return jsonify({"success": False, "message": "Verification code has expired. Please request a new code."}), 400

    if record['otp'] != otp:
        return jsonify({"success": False, "message": "Invalid verification code. Please check and try again."}), 400

    # Reset password
    pwd_hash = generate_password_hash(new_password)
    query_db("UPDATE users SET password_hash = ? WHERE LOWER(username) = ?", (pwd_hash, username), commit=True)
    del PASSWORD_RESET_OTPS[username]

    return jsonify({
        "success": True,
        "message": "Password updated successfully. You can now log in with your new password."
    })

# ==============================================================================
# Administrator APIs
# ==============================================================================

@app.route('/api/admin/stats', methods=['GET'])
@role_required(['admin'])
def api_admin_stats():
    teachers_count = query_db("SELECT COUNT(*) as count FROM users WHERE role = 'teacher'", one=True)['count']
    students_count = query_db("SELECT COUNT(*) as count FROM users WHERE role = 'student'", one=True)['count']
    depts_count = query_db("SELECT COUNT(*) as count FROM departments", one=True)['count']
    subjects_count = query_db("SELECT COUNT(*) as count FROM subjects", one=True)['count']
    rooms_count = query_db("SELECT COUNT(*) as count FROM classrooms", one=True)['count']
    timetables_count = query_db("SELECT COUNT(*) as count FROM timetables WHERE published = 1", one=True)['count']
    pending_swaps = query_db("SELECT COUNT(*) as count FROM swap_requests WHERE status = 'pending'", one=True)['count']
    
    # Conflict check across all timetables
    all_slots = query_db("SELECT day, period, teacher_id, classroom_id FROM timetable_slots WHERE teacher_id IS NOT NULL")
    seen_teachers = set()
    seen_rooms = set()
    conflicts_count = 0
    
    for s in all_slots:
        t_key = f"{s['teacher_id']}_{s['day']}_{s['period']}"
        r_key = f"{s['classroom_id']}_{s['day']}_{s['period']}"
        if t_key in seen_teachers:
            conflicts_count += 1
        seen_teachers.add(t_key)
        if s['classroom_id']:
            if r_key in seen_rooms:
                conflicts_count += 1
            seen_rooms.add(r_key)

    # Recent activities
    recent_swaps = query_db(
        "SELECT * FROM swap_history ORDER BY executed_at DESC LIMIT 5"
    )
    recent_announcements = query_db(
        "SELECT * FROM announcements ORDER BY created_at DESC LIMIT 5"
    )

    return jsonify({
        "success": True,
        "counts": {
            "teachers": teachers_count,
            "students": students_count,
            "departments": depts_count,
            "subjects": subjects_count,
            "classrooms": rooms_count,
            "timetables": timetables_count,
            "pending_swaps": pending_swaps,
            "conflicts": conflicts_count
        },
        "recent_swaps": recent_swaps,
        "recent_announcements": recent_announcements
    })

# Teachers CRUD
@app.route('/api/teachers', methods=['GET', 'POST'])
@login_required
def api_teachers():
    if request.method == 'GET':
        dept_id = request.args.get('department_id')
        search = (request.args.get('search') or '').strip().lower()
        
        sql = """
            SELECT u.id, u.name, u.username, u.email, u.phone, u.department_id,
                   d.name as department_name, d.code as department_code,
                   (SELECT COUNT(*) FROM timetable_slots ts 
                    JOIN timetables t ON ts.timetable_id = t.id 
                    WHERE ts.teacher_id = u.id AND ts.slot_type != 'activity' AND t.published = 1) as assigned_periods
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.role = 'teacher'
        """
        params = []
        if dept_id and dept_id != 'all':
            sql += " AND u.department_id = ?"
            params.append(dept_id)
            
        teachers = query_db(sql, params)

        # Retrieve distinct classes and subjects taught by each teacher from latest published timetables
        slot_classes = query_db(
            """
            SELECT DISTINCT ts.teacher_id, sub.code as subject_code, sub.name as subject_name,
                   d.code as dept_code, t.year, t.semester, t.section
            FROM timetable_slots ts
            JOIN timetables t ON ts.timetable_id = t.id
            JOIN departments d ON t.department_id = d.id
            LEFT JOIN subjects sub ON ts.subject_id = sub.id
            WHERE ts.teacher_id IS NOT NULL AND t.published = 1
            ORDER BY sub.code ASC
            """
        )
        classes_by_teacher = {}
        for sc in slot_classes:
            tid = sc['teacher_id']
            if tid not in classes_by_teacher:
                classes_by_teacher[tid] = []
            sec_label = f"Sec {sc['section']}" if sc.get('section') else ""
            classes_by_teacher[tid].append({
                "subject_code": sc['subject_code'] or "Course",
                "subject_name": sc['subject_name'] or "",
                "cohort": f"{sc['dept_code']} Y{sc['year']} S{sc['semester']} {sec_label}".strip()
            })

        # Also get assigned subjects from subjects table if not yet scheduled in published slots
        assigned_subs = query_db("SELECT teacher_id, code as subject_code, name as subject_name FROM subjects WHERE teacher_id IS NOT NULL")
        assigned_by_teacher = {}
        for asub in assigned_subs:
            tid = asub['teacher_id']
            if tid not in assigned_by_teacher:
                assigned_by_teacher[tid] = []
            assigned_by_teacher[tid].append({
                "subject_code": asub['subject_code'],
                "subject_name": asub['subject_name'],
                "cohort": "Curriculum"
            })

        for t in teachers:
            # If teacher has published timetable slots, that's their exact current classes
            t_classes = classes_by_teacher.get(t['id'], [])
            if not t_classes:
                # Fallback to curriculum subjects assigned to them
                t_classes = assigned_by_teacher.get(t['id'], [])
            t['classes_taken'] = t_classes
            t['classes_summary'] = [f"{c['subject_code']} ({c['cohort']})" for c in t_classes]

        if search:
            teachers = [
                t for t in teachers
                if search in t['name'].lower() 
                or search in (t['email'] or '').lower() 
                or search in (t['department_code'] or '').lower()
                or any(search in c['subject_code'].lower() or search in c['subject_name'].lower() for c in t['classes_taken'])
            ]
        return jsonify({"success": True, "teachers": teachers})

    # POST (Admin only)
    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    username = (data.get('username') or '').strip().lower()
    password = data.get('password') or 'teacher123'
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    dept_id = data.get('department_id')

    if not name or not username:
        return jsonify({"success": False, "message": "Faculty name and username are required."}), 400

    existing = query_db("SELECT id FROM users WHERE LOWER(username) = ?", (username,), one=True)
    if existing:
        return jsonify({"success": False, "message": "Username already exists in faculty directory."}), 400

    t_id = f"tch_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()
    pwd_hash = generate_password_hash(password)

    query_db(
        "INSERT INTO users (id, username, password_hash, role, name, email, phone, department_id, created_at) VALUES (?, ?, ?, 'teacher', ?, ?, ?, ?, ?)",
        (t_id, username, pwd_hash, name, email, phone, dept_id, now),
        commit=True
    )
    return jsonify({"success": True, "message": f"Faculty member '{name}' added successfully."})

@app.route('/api/teachers/<id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_teacher_detail(id):
    if request.method == 'GET':
        teacher = query_db(
            """
            SELECT u.id, u.name, u.username, u.email, u.phone, u.department_id,
                   d.name as department_name, d.code as department_code
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.id = ? AND u.role = 'teacher'
            """,
            (id,), one=True
        )
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404
        
        # Get teaching subjects
        subjects = query_db("SELECT * FROM subjects WHERE teacher_id = ?", (id,))
        
        # Get timetable slots from published timetables (dynamically reflects current published routine)
        slots = query_db(
            """
            SELECT ts.*, sub.name as subject_name, sub.code as subject_code,
                   cls.name as classroom_name, d.code as dept_code, t.year, t.semester, t.section
            FROM timetable_slots ts
            JOIN timetables t ON ts.timetable_id = t.id
            JOIN departments d ON t.department_id = d.id
            LEFT JOIN subjects sub ON ts.subject_id = sub.id
            LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
            WHERE ts.teacher_id = ? AND t.published = 1
            ORDER BY ts.period ASC
            """,
            (id,)
        )
        if not slots:
            slots = query_db(
                """
                SELECT ts.*, sub.name as subject_name, sub.code as subject_code,
                       cls.name as classroom_name, d.code as dept_code, t.year, t.semester, t.section
                FROM timetable_slots ts
                JOIN timetables t ON ts.timetable_id = t.id
                JOIN departments d ON t.department_id = d.id
                LEFT JOIN subjects sub ON ts.subject_id = sub.id
                LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
                WHERE ts.teacher_id = ?
                ORDER BY ts.period ASC
                """,
                (id,)
            )
        return jsonify({"success": True, "teacher": teacher, "subjects": subjects, "slots": slots})

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    if request.method == 'PUT':
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()
        dept_id = data.get('department_id')
        password = data.get('password')

        if password:
            pwd_hash = generate_password_hash(password)
            query_db(
                "UPDATE users SET name = ?, email = ?, phone = ?, department_id = ?, password_hash = ? WHERE id = ?",
                (name, email, phone, dept_id, pwd_hash, id), commit=True
            )
        else:
            query_db(
                "UPDATE users SET name = ?, email = ?, phone = ?, department_id = ? WHERE id = ?",
                (name, email, phone, dept_id, id), commit=True
            )
        return jsonify({"success": True, "message": "Faculty profile updated."})

    if request.method == 'DELETE':
        query_db("DELETE FROM users WHERE id = ? AND role = 'teacher'", (id,), commit=True)
        # Clear teacher_id from subjects and slots
        query_db("UPDATE subjects SET teacher_id = NULL WHERE teacher_id = ?", (id,), commit=True)
        query_db("UPDATE timetable_slots SET teacher_id = NULL WHERE teacher_id = ?", (id,), commit=True)
        return jsonify({"success": True, "message": "Faculty member removed from directory."})

# Students CRUD
@app.route('/api/students', methods=['GET', 'POST'])
@login_required
def api_students():
    if request.method == 'GET':
        dept_id = request.args.get('department_id')
        year = request.args.get('year')
        semester = request.args.get('semester')
        search = (request.args.get('search') or '').strip().lower()

        sql = """
            SELECT u.id, u.name, u.username, u.email, u.phone, u.roll_no,
                   u.department_id, u.year, u.semester, u.section,
                   d.name as department_name, d.code as department_code
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            WHERE u.role = 'student'
        """
        params = []
        if dept_id and dept_id != 'all':
            sql += " AND u.department_id = ?"
            params.append(dept_id)
        if year and year != 'all':
            sql += " AND u.year = ?"
            params.append(int(year))
        if semester and semester != 'all':
            sql += " AND u.semester = ?"
            params.append(int(semester))

        students = query_db(sql, params)
        if search:
            students = [
                s for s in students
                if search in s['name'].lower() or search in (s['roll_no'] or '').lower() or search in s['username'].lower()
            ]
        return jsonify({"success": True, "students": students})

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    roll_no = (data.get('roll_no') or '').strip()
    username = (data.get('username') or '').strip().lower()
    password = data.get('password') or 'student123'
    email = (data.get('email') or '').strip()
    dept_id = data.get('department_id')
    year = int(data.get('year', 1))
    sem = int(data.get('semester', 1))
    sec = (data.get('section') or 'A').strip()

    if not name or not username:
        return jsonify({"success": False, "message": "Student name and username are required."}), 400

    existing = query_db("SELECT id FROM users WHERE LOWER(username) = ?", (username,), one=True)
    if existing:
        return jsonify({"success": False, "message": "Student username already in use."}), 400

    s_id = f"stu_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()
    pwd_hash = generate_password_hash(password)

    query_db(
        """
        INSERT INTO users (id, username, password_hash, role, name, email, roll_no, department_id, year, semester, section, created_at)
        VALUES (?, ?, ?, 'student', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (s_id, username, pwd_hash, name, email, roll_no, dept_id, year, sem, sec, now),
        commit=True
    )
    return jsonify({"success": True, "message": f"Student '{name}' registered successfully."})

@app.route('/api/students/<id>', methods=['PUT', 'DELETE'])
@role_required(['admin'])
def api_student_detail(id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        roll_no = (data.get('roll_no') or '').strip()
        email = (data.get('email') or '').strip()
        dept_id = data.get('department_id')
        year = int(data.get('year', 1))
        sem = int(data.get('semester', 1))
        sec = (data.get('section') or 'A').strip()
        password = data.get('password')

        if password:
            pwd_hash = generate_password_hash(password)
            query_db(
                """
                UPDATE users SET name = ?, roll_no = ?, email = ?, department_id = ?,
                                 year = ?, semester = ?, section = ?, password_hash = ?
                WHERE id = ? AND role = 'student'
                """,
                (name, roll_no, email, dept_id, year, sem, sec, pwd_hash, id), commit=True
            )
        else:
            query_db(
                """
                UPDATE users SET name = ?, roll_no = ?, email = ?, department_id = ?,
                                 year = ?, semester = ?, section = ?
                WHERE id = ? AND role = 'student'
                """,
                (name, roll_no, email, dept_id, year, sem, sec, id), commit=True
            )
        return jsonify({"success": True, "message": "Student record updated."})

    if request.method == 'DELETE':
        query_db("DELETE FROM users WHERE id = ? AND role = 'student'", (id,), commit=True)
        return jsonify({"success": True, "message": "Student deleted."})

# Departments CRUD
@app.route('/api/departments', methods=['GET', 'POST'])
@login_required
def api_departments():
    if request.method == 'GET':
        depts = query_db(
            """
            SELECT d.*,
                   (SELECT COUNT(*) FROM users u WHERE u.department_id = d.id AND u.role = 'teacher') as faculty_count,
                   (SELECT COUNT(*) FROM subjects s WHERE s.department_id = d.id) as subjects_count,
                   (SELECT COUNT(*) FROM users u WHERE u.department_id = d.id AND u.role = 'student') as students_count
            FROM departments d
            """
        )
        return jsonify({"success": True, "departments": depts})

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    code = (data.get('code') or '').strip().upper()

    if not name or not code:
        return jsonify({"success": False, "message": "Department name and code are required."}), 400

    d_id = f"dept_{int(datetime.datetime.now().timestamp() * 1000)}"
    query_db("INSERT INTO departments (id, name, code) VALUES (?, ?, ?)", (d_id, name, code), commit=True)
    return jsonify({"success": True, "message": f"Department '{code}' created."})

@app.route('/api/departments/<id>', methods=['PUT', 'DELETE'])
@role_required(['admin'])
def api_department_detail(id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        code = (data.get('code') or '').strip().upper()
        query_db("UPDATE departments SET name = ?, code = ? WHERE id = ?", (name, code, id), commit=True)
        return jsonify({"success": True, "message": "Department updated."})

    if request.method == 'DELETE':
        query_db("DELETE FROM departments WHERE id = ?", (id,), commit=True)
        return jsonify({"success": True, "message": "Department deleted."})

# Subjects CRUD
@app.route('/api/subjects', methods=['GET', 'POST'])
@login_required
def api_subjects():
    if request.method == 'GET':
        dept_id = request.args.get('department_id')
        year = request.args.get('year')
        sem = request.args.get('semester')

        sql = """
            SELECT s.*, d.name as department_name, d.code as department_code,
                   u.name as teacher_name
            FROM subjects s
            LEFT JOIN departments d ON s.department_id = d.id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE 1=1
        """
        params = []
        if dept_id and dept_id != 'all':
            sql += " AND s.department_id = ?"
            params.append(dept_id)
        if year and year != 'all':
            sql += " AND s.year = ?"
            params.append(int(year))
        if sem and sem != 'all':
            sql += " AND s.semester = ?"
            params.append(int(sem))

        subjects = query_db(sql, params)
        return jsonify({"success": True, "subjects": subjects})

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    code = (data.get('code') or '').strip().upper()
    dept_id = data.get('department_id')
    year = int(data.get('year', 1))
    sem = int(data.get('semester', 1))
    sub_type = data.get('type', 'theory')
    hours = int(data.get('hours_per_week', 4))
    t_id = data.get('teacher_id')

    sub_id = f"sub_{int(datetime.datetime.now().timestamp() * 1000)}"
    query_db(
        """
        INSERT INTO subjects (id, name, code, department_id, year, semester, type, hours_per_week, teacher_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (sub_id, name, code, dept_id, year, sem, sub_type, hours, t_id),
        commit=True
    )
    return jsonify({"success": True, "message": f"Subject '{code}' added to curriculum."})

@app.route('/api/subjects/<id>', methods=['PUT', 'DELETE'])
@role_required(['admin'])
def api_subject_detail(id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        query_db(
            """
            UPDATE subjects SET name = ?, code = ?, department_id = ?, year = ?, semester = ?,
                               type = ?, hours_per_week = ?, teacher_id = ?
            WHERE id = ?
            """,
            (
                data.get('name').strip(),
                data.get('code').strip().upper(),
                data.get('department_id'),
                int(data.get('year')),
                int(data.get('semester')),
                data.get('type'),
                int(data.get('hours_per_week')),
                data.get('teacher_id') or None,
                id
            ),
            commit=True
        )
        return jsonify({"success": True, "message": "Subject updated."})

    if request.method == 'DELETE':
        query_db("DELETE FROM subjects WHERE id = ?", (id,), commit=True)
        return jsonify({"success": True, "message": "Subject removed."})

# Classrooms CRUD
@app.route('/api/classrooms', methods=['GET', 'POST'])
@login_required
def api_classrooms():
    if request.method == 'GET':
        rooms = query_db("SELECT * FROM classrooms ORDER BY building, name")
        return jsonify({"success": True, "classrooms": rooms})

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    c_type = data.get('type', 'classroom')
    cap = int(data.get('capacity', 60))
    bld = (data.get('building') or 'Main Block').strip()

    c_id = f"cls_{int(datetime.datetime.now().timestamp() * 1000)}"
    query_db(
        "INSERT INTO classrooms (id, name, type, capacity, building) VALUES (?, ?, ?, ?, ?)",
        (c_id, name, c_type, cap, bld), commit=True
    )
    return jsonify({"success": True, "message": f"Facility '{name}' configured."})

@app.route('/api/classrooms/<id>', methods=['PUT', 'DELETE'])
@role_required(['admin'])
def api_classroom_detail(id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        query_db(
            "UPDATE classrooms SET name = ?, type = ?, capacity = ?, building = ? WHERE id = ?",
            (data.get('name'), data.get('type'), int(data.get('capacity')), data.get('building'), id),
            commit=True
        )
        return jsonify({"success": True, "message": "Facility updated."})

    if request.method == 'DELETE':
        query_db("DELETE FROM classrooms WHERE id = ?", (id,), commit=True)
        return jsonify({"success": True, "message": "Facility removed."})

# ==============================================================================
# Timetable Management & Generation APIs
# ==============================================================================

@app.route('/api/timetables', methods=['GET'])
@login_required
def api_get_timetable():
    dept_id = request.args.get('department_id')
    year = request.args.get('year')
    sem = request.args.get('semester')
    section = request.args.get('section')

    if not dept_id or not year or not sem:
        # If no specific cohort requested, return all available timetables
        all_tt = query_db(
            """
            SELECT t.*, d.name as department_name, d.code as department_code
            FROM timetables t
            JOIN departments d ON t.department_id = d.id
            ORDER BY d.code, t.year, t.semester, t.section
            """
        )
        return jsonify({"success": True, "timetables": all_tt})

    sql = """
        SELECT t.*, d.name as department_name, d.code as department_code
        FROM timetables t
        JOIN departments d ON t.department_id = d.id
        WHERE t.department_id = ? AND t.year = ? AND t.semester = ?
    """
    params = [dept_id, int(year), int(sem)]
    if section:
        sql += " AND t.section = ?"
        params.append(section)
    sql += " LIMIT 1"

    tt = query_db(sql, params, one=True)

    if not tt:
        return jsonify({"success": True, "timetable": None, "slots": []})

    slots = query_db(
        """
        SELECT ts.*, sub.name as subject_name, sub.code as subject_code, sub.type as subject_type,
               u.name as teacher_name, cls.name as classroom_name, cls.building as classroom_building
        FROM timetable_slots ts
        LEFT JOIN subjects sub ON ts.subject_id = sub.id
        LEFT JOIN users u ON ts.teacher_id = u.id
        LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
        WHERE ts.timetable_id = ?
        ORDER BY ts.period ASC
        """,
        (tt['id'],)
    )

    return jsonify({
        "success": True,
        "timetable": tt,
        "slots": slots,
        "periods_config": get_periods_config(),
        "days_config": get_days_config()
    })

@app.route('/api/timetables/cohorts', methods=['GET'])
@login_required
def api_timetable_cohorts():
    cohorts = query_db(
        """
        SELECT t.id, t.department_id, t.year, t.semester, t.section, t.published,
               d.name as department_name, d.code as department_code,
               (SELECT COUNT(*) FROM timetable_slots ts WHERE ts.timetable_id = t.id) as total_slots
        FROM timetables t
        JOIN departments d ON t.department_id = d.id
        ORDER BY d.code, t.year, t.semester, t.section
        """
    )
    return jsonify({"success": True, "cohorts": cohorts})

@app.route('/api/timetables/generate', methods=['POST'])
@role_required(['admin'])
def api_generate_timetable():
    data = request.get_json() or {}
    dept_id = data.get('department_id')
    year = data.get('year')
    sem = data.get('semester')
    section = data.get('section', 'A')

    if not dept_id or not year or not sem:
        return jsonify({"success": False, "message": "department_id, year, and semester required."}), 400

    result = generate_timetable(dept_id, year, sem, section)
    if not result['success']:
        return jsonify({"success": False, "errors": result['errors']}), 422

    tt_id = result['timetable_id']
    now = datetime.datetime.now().isoformat()

    # Save to database
    legacy_tt_id = f"tt_{dept_id}_{year}_{sem}"
    query_db("DELETE FROM timetable_slots WHERE timetable_id = ? OR timetable_id = ?", (tt_id, legacy_tt_id), commit=True)
    query_db("DELETE FROM timetables WHERE id = ? OR id = ?", (tt_id, legacy_tt_id), commit=True)

    query_db(
        "INSERT INTO timetables (id, department_id, year, semester, section, published, generated_at, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
        (tt_id, dept_id, int(year), int(sem), section, now, now),
        commit=True
    )

    for slot in result['slots']:
        query_db(
            """
            INSERT INTO timetable_slots (timetable_id, day, period, subject_id, teacher_id, classroom_id, slot_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tt_id, slot['day'], slot['period'],
                slot.get('subject_id'), slot.get('teacher_id'),
                slot.get('classroom_id'), slot.get('slot_type', 'regular')
            ),
            commit=True
        )

    return jsonify({
        "success": True,
        "message": f"Conflict-free timetable generated for {dept_id} Year {year} Sem {sem} Sec {section}.",
        "timetable_id": tt_id,
        "slot_count": len(result['slots'])
    })

@app.route('/api/timetables/<id>/publish', methods=['POST'])
@role_required(['admin'])
def api_publish_timetable(id):
    tt = query_db("SELECT * FROM timetables WHERE id = ?", (id,), one=True)
    if not tt:
        return jsonify({"error": "Timetable not found"}), 404

    # Deactivate any previous published timetable for this same cohort so only the latest is active
    sec = tt.get('section') or 'A'
    query_db(
        "UPDATE timetables SET published = 0 WHERE department_id = ? AND year = ? AND semester = ? AND (section = ? OR section IS NULL) AND id != ?",
        (tt['department_id'], tt['year'], tt['semester'], sec, id),
        commit=True
    )
    query_db("UPDATE timetables SET published = 1, updated_at = ? WHERE id = ?", (datetime.datetime.now().isoformat(), id), commit=True)

    dept = query_db("SELECT code FROM departments WHERE id = ?", (tt['department_id'],), one=True)
    dept_code = dept['code'] if dept else "Cohort"

    # Broadcast notification to enrolled students
    now = datetime.datetime.now().isoformat()
    query_db(
        "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, 'all_students', 'student', ?, ?, '/student#timetable', 0, ?)",
        (
            f"not_{int(datetime.datetime.now().timestamp()*1000)}",
            f"Timetable Published: {dept_code} Year {tt['year']} Sem {tt['semester']}",
            f"The official academic class timetable for {dept_code} Year {tt['year']} Sem {tt['semester']} is now published and active.",
            now
        ),
        commit=True
    )

    return jsonify({"success": True, "message": "Timetable published. Cohort routines are now live."})

@app.route('/api/timetables/<id>/unpublish', methods=['POST'])
@role_required(['admin'])
def api_unpublish_timetable(id):
    query_db("UPDATE timetables SET published = 0, updated_at = ? WHERE id = ?", (datetime.datetime.now().isoformat(), id), commit=True)
    return jsonify({"success": True, "message": "Timetable reverted to draft status."})

@app.route('/api/timetables/<id>', methods=['DELETE'])
@role_required(['admin'])
def api_delete_timetable(id):
    query_db("DELETE FROM timetable_slots WHERE timetable_id = ?", (id,), commit=True)
    query_db("DELETE FROM timetables WHERE id = ?", (id,), commit=True)
    return jsonify({"success": True, "message": "Timetable and associated period slots removed."})

@app.route('/api/timetables/slots/<int:slot_id>', methods=['PUT', 'DELETE'])
@role_required(['admin'])
def api_update_slot(slot_id):
    if request.method == 'DELETE':
        query_db("DELETE FROM timetable_slots WHERE id = ?", (slot_id,), commit=True)
        return jsonify({"success": True, "message": "Period slot cleared."})

    data = request.get_json() or {}
    sub_id = data.get('subject_id') or None
    t_id = data.get('teacher_id') or None
    r_id = data.get('classroom_id') or None
    slot_type = data.get('slot_type', 'regular')

    slot = query_db("SELECT * FROM timetable_slots WHERE id = ?", (slot_id,), one=True)
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    # Cross-cohort and cross-semester conflict check
    if t_id:
        t_conflict = query_db(
            """
            SELECT ts.id, ts.day, ts.period, t.year, t.semester, t.section, d.code as dept_code, u.name as teacher_name
            FROM timetable_slots ts
            JOIN timetables t ON ts.timetable_id = t.id
            JOIN departments d ON t.department_id = d.id
            LEFT JOIN users u ON ts.teacher_id = u.id
            WHERE ts.day = ? AND ts.period = ? AND ts.teacher_id = ? AND ts.id != ?
            """,
            (slot['day'], slot['period'], t_id, slot_id),
            one=True
        )
        if t_conflict:
            t_name = t_conflict.get('teacher_name') or 'Faculty'
            sec_lbl = t_conflict.get('section') or 'A'
            return jsonify({
                "success": False,
                "message": f"Conflict Warning: {t_name} is already teaching {t_conflict['dept_code']} Y{t_conflict['year']}S{t_conflict['semester']} Sec {sec_lbl} on {slot['day']} Period {slot['period']}."
            }), 409

    if r_id:
        r_conflict = query_db(
            """
            SELECT ts.id, ts.day, ts.period, t.year, t.semester, t.section, d.code as dept_code, cls.name as classroom_name
            FROM timetable_slots ts
            JOIN timetables t ON ts.timetable_id = t.id
            JOIN departments d ON t.department_id = d.id
            LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
            WHERE ts.day = ? AND ts.period = ? AND ts.classroom_id = ? AND ts.id != ?
            """,
            (slot['day'], slot['period'], r_id, slot_id),
            one=True
        )
        if r_conflict:
            r_name = r_conflict.get('classroom_name') or 'Facility'
            sec_lbl = r_conflict.get('section') or 'A'
            return jsonify({
                "success": False,
                "message": f"Conflict Warning: Facility {r_name} is already booked for {r_conflict['dept_code']} Y{r_conflict['year']}S{r_conflict['semester']} Sec {sec_lbl} on {slot['day']} Period {slot['period']}."
            }), 409

    query_db(
        "UPDATE timetable_slots SET subject_id = ?, teacher_id = ?, classroom_id = ?, slot_type = ? WHERE id = ?",
        (sub_id, t_id, r_id, slot_type, slot_id),
        commit=True
    )
    return jsonify({"success": True, "message": "Timetable period slot updated."})

# ==============================================================================
# Faculty Utilization & Workload Analytics APIs
# ==============================================================================

@app.route('/api/analytics/workload', methods=['GET'])
@role_required(['admin', 'teacher'])
def api_workload_analytics():
    dept_id = request.args.get('department_id')
    teacher_id = request.args.get('teacher_id')
    analytics = get_faculty_workload_analytics(department_id=dept_id, teacher_id=teacher_id)
    return jsonify({"success": True, "analytics": analytics})

# ==============================================================================
# Mutual Teacher-to-Teacher Class Swapping APIs
# ==============================================================================

@app.route('/api/swaps', methods=['GET'])
@login_required
def api_get_swaps():
    user = get_current_user()
    role = user['role']
    
    if role == 'admin':
        # Admin sees all swaps and swap audit history
        swaps = query_db(
            """
            SELECT sr.*,
                   u1.name as sender_name, u2.name as receiver_name,
                   sub1.name as sender_subject_name, sub1.code as sender_subject_code,
                   sub2.name as receiver_subject_name, sub2.code as receiver_subject_code
            FROM swap_requests sr
            JOIN users u1 ON sr.sender_teacher_id = u1.id
            JOIN users u2 ON sr.receiver_teacher_id = u2.id
            LEFT JOIN subjects sub1 ON sr.sender_subject_id = sub1.id
            LEFT JOIN subjects sub2 ON sr.receiver_subject_id = sub2.id
            ORDER BY sr.created_at DESC
            """
        )
        history = query_db("SELECT * FROM swap_history ORDER BY executed_at DESC LIMIT 50")
        return jsonify({"success": True, "swaps": swaps, "history": history})

    elif role == 'teacher':
        # Faculty sees incoming requests, outgoing requests, and history
        my_id = user['id']
        incoming = query_db(
            """
            SELECT sr.*, u.name as sender_name,
                   sub1.name as sender_subject_name, sub1.code as sender_subject_code,
                   sub2.name as receiver_subject_name, sub2.code as receiver_subject_code
            FROM swap_requests sr
            JOIN users u ON sr.sender_teacher_id = u.id
            LEFT JOIN subjects sub1 ON sr.sender_subject_id = sub1.id
            LEFT JOIN subjects sub2 ON sr.receiver_subject_id = sub2.id
            WHERE sr.receiver_teacher_id = ?
            ORDER BY sr.created_at DESC
            """,
            (my_id,)
        )
        outgoing = query_db(
            """
            SELECT sr.*, u.name as receiver_name,
                   sub1.name as sender_subject_name, sub1.code as sender_subject_code,
                   sub2.name as receiver_subject_name, sub2.code as receiver_subject_code
            FROM swap_requests sr
            JOIN users u ON sr.receiver_teacher_id = u.id
            LEFT JOIN subjects sub1 ON sr.sender_subject_id = sub1.id
            LEFT JOIN subjects sub2 ON sr.receiver_subject_id = sub2.id
            WHERE sr.sender_teacher_id = ?
            ORDER BY sr.created_at DESC
            """,
            (my_id,)
        )
        history = query_db(
            "SELECT * FROM swap_history WHERE sender_name = ? OR receiver_name = ? ORDER BY executed_at DESC",
            (user['name'], user['name'])
        )
        return jsonify({"success": True, "incoming": incoming, "outgoing": outgoing, "history": history})

    return jsonify({"error": "Forbidden"}), 403

@app.route('/api/swaps/request', methods=['POST'])
@role_required(['teacher'])
def api_create_swap():
    user = get_current_user()
    data = request.get_json() or {}
    
    receiver_teacher_id = data.get('receiver_teacher_id')
    sender_day = data.get('sender_day')
    sender_period = int(data.get('sender_period', 0))
    receiver_day = data.get('receiver_day')
    receiver_period = int(data.get('receiver_period', 0))
    sender_subject_id = data.get('sender_subject_id')
    receiver_subject_id = data.get('receiver_subject_id')
    reason = (data.get('reason') or '').strip()

    if not reason:
        return jsonify({"success": False, "message": "A justification reason is required for class swap proposals."}), 400

    result = create_swap_request(
        user['id'], receiver_teacher_id, sender_day, sender_period,
        receiver_day, receiver_period, sender_subject_id, receiver_subject_id, reason
    )
    return jsonify(result), (200 if result['success'] else 400)

@app.route('/api/swaps/respond', methods=['POST'])
@role_required(['teacher'])
def api_respond_swap():
    user = get_current_user()
    data = request.get_json() or {}
    swap_id = data.get('swap_id')
    action = data.get('action') # 'accept' or 'reject'
    rejection_reason = data.get('rejection_reason')

    result = process_swap_decision(swap_id, user['id'], action, rejection_reason)
    return jsonify(result), (200 if result['success'] else 400)

# ==============================================================================
# Calendar Module APIs
# ==============================================================================

@app.route('/api/calendar/events', methods=['GET'])
@login_required
def api_calendar_events():
    """
    Feeds standard FullCalendar JSON event objects:
    Regular classes, Institutional Events, Workshops, Extra Classes, Activities, and Swaps.
    Supports filtering to declutter the master calendar view.
    """
    user = get_current_user()
    role = user['role']

    # Filter parameters
    view_type = request.args.get('type', 'all')  # 'all', 'institutional', 'classes', 'recovery'
    dept_filter = request.args.get('department_id')
    year_filter = request.args.get('year')
    sem_filter = request.args.get('semester')
    sec_filter = request.args.get('section')
    teacher_filter = request.args.get('teacher_id')

    events_list = []
    
    # Map weekdays to reference ISO dates of current week
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday()) # Monday
    
    day_offset = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5
    }

    period_times = {
        1: ("09:00", "09:50"),
        2: ("09:50", "10:40"),
        3: ("10:40", "11:30"),
        4: ("11:45", "12:35"),
        5: ("12:35", "13:25"),
        6: ("14:00", "14:50"),
        7: ("14:50", "15:40"),
        8: ("15:40", "16:30")
    }

    # 1. Timetable classes (skip if view_type is 'institutional' or 'recovery')
    slots = []
    if view_type not in ('institutional', 'recovery'):
        if role == 'teacher':
            slots = query_db(
                """
                SELECT ts.*, sub.name as subject_name, sub.code as subject_code,
                       cls.name as classroom_name, d.code as dept_code, t.year, t.semester, t.section
                FROM timetable_slots ts
                JOIN timetables t ON ts.timetable_id = t.id
                JOIN departments d ON t.department_id = d.id
                LEFT JOIN subjects sub ON ts.subject_id = sub.id
                LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
                WHERE ts.teacher_id = ? AND t.published = 1
                """,
                (user['id'],)
            )
        elif role == 'student':
            slots = query_db(
                """
                SELECT ts.*, sub.name as subject_name, sub.code as subject_code,
                       cls.name as classroom_name, u.name as teacher_name, d.code as dept_code, t.year, t.semester, t.section
                FROM timetable_slots ts
                JOIN timetables t ON ts.timetable_id = t.id
                JOIN departments d ON t.department_id = d.id
                LEFT JOIN subjects sub ON ts.subject_id = sub.id
                LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
                LEFT JOIN users u ON ts.teacher_id = u.id
                WHERE t.department_id = ? AND t.year = ? AND t.semester = ? AND (t.section = ? OR t.section IS NULL) AND t.published = 1
                """,
                (user['department_id'], user['year'], user['semester'], user.get('section') or 'A')
            )
        else: # Admin (with optional filters)
            sql = """
                SELECT ts.*, sub.name as subject_name, sub.code as subject_code,
                       cls.name as classroom_name, u.name as teacher_name, d.code as dept_code, t.year, t.semester, t.section
                FROM timetable_slots ts
                JOIN timetables t ON ts.timetable_id = t.id
                JOIN departments d ON t.department_id = d.id
                LEFT JOIN subjects sub ON ts.subject_id = sub.id
                LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
                LEFT JOIN users u ON ts.teacher_id = u.id
                WHERE t.published = 1
            """
            params = []
            if dept_filter and dept_filter != 'all':
                sql += " AND t.department_id = ?"
                params.append(dept_filter)
            if year_filter and year_filter != 'all':
                sql += " AND t.year = ?"
                params.append(int(year_filter))
            if sem_filter and sem_filter != 'all':
                sql += " AND t.semester = ?"
                params.append(int(sem_filter))
            if sec_filter and sec_filter != 'all':
                sql += " AND t.section = ?"
                params.append(sec_filter)
            if teacher_filter and teacher_filter != 'all':
                sql += " AND ts.teacher_id = ?"
                params.append(teacher_filter)
            slots = query_db(sql, params)

        for s in slots:
            if s['day'] in day_offset and s['period'] in period_times:
                event_date = start_of_week + datetime.timedelta(days=day_offset[s['day']])
                t_start, t_end = period_times[s['period']]
                
                is_lab = s.get('slot_type') == 'lab'
                sec_lbl = f" Sec {s['section']}" if s.get('section') else ""
                cohort_tag = f"[{s.get('dept_code', '')} S{s.get('semester', '')}{sec_lbl}]"
                room_tag = f" - {s.get('classroom_name')}" if s.get('classroom_name') else ""
                title = f"{cohort_tag} {s.get('subject_code') or 'Class'}{room_tag}"
                color = "#059669" if is_lab else "#4f46e5"

                events_list.append({
                    "id": f"slot_{s['id']}",
                    "title": title,
                    "start": f"{event_date}T{t_start}:00",
                    "end": f"{event_date}T{t_end}:00",
                    "backgroundColor": color,
                    "borderColor": color,
                    "extendedProps": {
                        "type": "lab" if is_lab else "class",
                        "subject": s.get('subject_name'),
                        "room": s.get('classroom_name'),
                        "faculty": s.get('teacher_name'),
                        "cohort": f"{s.get('dept_code')} Sem {s.get('semester')}{sec_lbl}"
                    }
                })

    # 2. Academic Events (Workshops, Seminars, Holidays) - included unless view_type is 'classes'
    if view_type != 'classes':
        events = query_db("SELECT * FROM academic_events")
        for ev in events:
            color = "#d97706" if ev['event_type'] == 'workshop' else "#dc2626" if ev['event_type'] == 'holiday' else "#0284c7"
            events_list.append({
                "id": f"ev_{ev['id']}",
                "title": f"[{ev['event_type'].upper()}] {ev['title']}",
                "start": f"{ev['event_date']}T{ev['start_time'] or '09:00'}:00",
                "end": f"{ev['event_date']}T{ev['end_time'] or '17:00'}:00",
                "backgroundColor": color,
                "borderColor": color,
                "extendedProps": {
                    "type": ev['event_type'],
                    "description": ev['description'],
                    "periods_lost": ev['periods_lost']
                }
            })

    # 3. Extra Classes (Lost Class Recovery) - included unless view_type is 'institutional'
    if view_type in ('all', 'recovery', 'classes'):
        extra_classes = query_db(
            """
            SELECT ec.*, sub.name as subject_name, sub.code as subject_code,
                   cls.name as classroom_name, u.name as teacher_name
            FROM extra_classes ec
            LEFT JOIN subjects sub ON ec.subject_id = sub.id
            LEFT JOIN classrooms cls ON ec.classroom_id = cls.id
            LEFT JOIN users u ON ec.teacher_id = u.id
            """
        )
        for ext in extra_classes:
            p = ext['period']
            t_start, t_end = period_times.get(p, ("16:00", "17:00"))
            events_list.append({
                "id": f"ext_{ext['id']}",
                "title": f"[RECOVERY] {ext['subject_code']} ({ext.get('classroom_name') or 'Room'})",
                "start": f"{ext['replacement_date']}T{t_start}:00",
                "end": f"{ext['replacement_date']}T{t_end}:00",
                "backgroundColor": "#7c3aed",
                "borderColor": "#6d28d9",
                "extendedProps": {
                    "type": "extra_class",
                    "subject": ext['subject_name'],
                    "room": ext['classroom_name'],
                    "faculty": ext['teacher_name']
                }
            })

    # 4. Activity Periods
    activities = query_db("SELECT * FROM activity_periods")
    for act in activities:
        if act['day'] in day_offset and act['period'] in period_times:
            event_date = start_of_week + datetime.timedelta(days=day_offset[act['day']])
            t_start, t_end = period_times[act['period']]
            events_list.append({
                "id": f"act_{act['id']}",
                "title": f"[{act['activity_type'].upper()}] {act['name']}",
                "start": f"{event_date}T{t_start}:00",
                "end": f"{event_date}T{t_end}:00",
                "backgroundColor": "#059669",
                "borderColor": "#047857",
                "extendedProps": {
                    "type": "activity",
                    "venue": act.get('venue')
                }
            })

    return jsonify(events_list)

# ==============================================================================
# Academic Progress (Syllabus & Assignments) APIs
# ==============================================================================

@app.route('/api/syllabus/<subject_id>', methods=['GET'])
@login_required
def api_get_syllabus(subject_id):
    topics = query_db(
        "SELECT * FROM syllabus_topics WHERE subject_id = ? ORDER BY chapter, created_at",
        (subject_id,)
    )
    total = len(topics)
    completed = sum(1 for t in topics if t['status'] == 'completed')
    pct = round((completed / total) * 100, 1) if total > 0 else 0
    return jsonify({
        "success": True,
        "topics": topics,
        "stats": {
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "completion_pct": pct
        }
    })

@app.route('/api/syllabus', methods=['POST'])
@role_required(['teacher', 'admin'])
def api_add_syllabus():
    user = get_current_user()
    data = request.get_json() or {}
    sub_id = data.get('subject_id')
    title = (data.get('title') or '').strip()
    chapter = (data.get('chapter') or 'Module 1').strip()
    notes = (data.get('notes') or '').strip()

    if not sub_id or not title:
        return jsonify({"success": False, "message": "Subject and topic title required."}), 400

    syl_id = f"syl_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()
    query_db(
        "INSERT INTO syllabus_topics (id, subject_id, teacher_id, title, chapter, status, notes, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
        (syl_id, sub_id, user['id'], title, chapter, notes, now),
        commit=True
    )
    return jsonify({"success": True, "message": f"Topic '{title}' added to syllabus."})

@app.route('/api/syllabus/<id>/toggle', methods=['PUT'])
@role_required(['teacher', 'admin'])
def api_toggle_syllabus(id):
    topic = query_db("SELECT * FROM syllabus_topics WHERE id = ?", (id,), one=True)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    data = request.get_json() or {}
    new_status = 'completed' if topic['status'] == 'pending' else 'pending'
    comp_date = datetime.date.today().isoformat() if new_status == 'completed' else None
    notes = data.get('notes') if 'notes' in data else topic['notes']

    query_db(
        "UPDATE syllabus_topics SET status = ?, completion_date = ?, notes = ? WHERE id = ?",
        (new_status, comp_date, notes, id),
        commit=True
    )
    return jsonify({"success": True, "new_status": new_status, "completion_date": comp_date})

@app.route('/api/assignments', methods=['GET', 'POST'])
@login_required
def api_assignments():
    user = get_current_user()
    role = user['role']

    if request.method == 'GET':
        if role == 'teacher':
            assignments = query_db(
                """
                SELECT a.*, sub.name as subject_name, sub.code as subject_code,
                       (SELECT COUNT(*) FROM assignment_submissions asub WHERE asub.assignment_id = a.id) as total_submissions
                FROM assignments a
                JOIN subjects sub ON a.subject_id = sub.id
                WHERE a.teacher_id = ?
                ORDER BY a.due_date ASC
                """,
                (user['id'],)
            )
        elif role == 'student':
            assignments = query_db(
                """
                SELECT a.*, sub.name as subject_name, sub.code as subject_code, u.name as teacher_name,
                       asub.status as my_status, asub.submission_date as my_submission_date, asub.grade as my_grade
                FROM assignments a
                JOIN subjects sub ON a.subject_id = sub.id
                JOIN users u ON a.teacher_id = u.id
                LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.student_id = ?
                WHERE a.department_id = ? AND a.year = ? AND a.semester = ?
                ORDER BY a.due_date ASC
                """,
                (user['id'], user['department_id'], user['year'], user['semester'])
            )
        else: # Admin
            assignments = query_db(
                """
                SELECT a.*, sub.name as subject_name, sub.code as subject_code, u.name as teacher_name
                FROM assignments a
                JOIN subjects sub ON a.subject_id = sub.id
                JOIN users u ON a.teacher_id = u.id
                ORDER BY a.due_date ASC
                """
            )
        return jsonify({"success": True, "assignments": assignments})

    # POST (Teacher only)
    if role not in ('teacher', 'admin'):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    sub_id = data.get('subject_id')
    title = (data.get('title') or '').strip()
    desc = (data.get('description') or '').strip()
    due_date = data.get('due_date')

    sub = query_db("SELECT department_id, year, semester FROM subjects WHERE id = ?", (sub_id,), one=True)
    if not sub or not title or not due_date:
        return jsonify({"success": False, "message": "Subject, title, and due date are required."}), 400

    asn_id = f"asn_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()
    today_date = datetime.date.today().isoformat()

    query_db(
        """
        INSERT INTO assignments (id, subject_id, teacher_id, department_id, year, semester, section, title, description, issue_date, due_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'A', ?, ?, ?, ?, ?)
        """,
        (asn_id, sub_id, user['id'], sub['department_id'], sub['year'], sub['semester'], title, desc, today_date, due_date, now),
        commit=True
    )
    return jsonify({"success": True, "message": f"Assignment '{title}' published to students."})

@app.route('/api/student/assignments/<id>/submit', methods=['POST'])
@role_required(['student'])
def api_submit_assignment(id):
    user = get_current_user()
    data = request.get_json() or {}
    notes = (data.get('notes') or 'Submitted assignment on time.').strip()

    now = datetime.datetime.now().isoformat()
    subm_id = f"subm_{int(datetime.datetime.now().timestamp() * 1000)}"

    query_db(
        """
        INSERT OR REPLACE INTO assignment_submissions (id, assignment_id, student_id, submission_date, status, notes)
        VALUES (?, ?, ?, ?, 'submitted', ?)
        """,
        (subm_id, id, user['id'], now, notes),
        commit=True
    )
    return jsonify({"success": True, "message": "Assignment submission recorded successfully."})

# ==============================================================================
# Events, Workshops & Lost Class Recovery APIs
# ==============================================================================

@app.route('/api/events', methods=['GET', 'POST'])
@login_required
def api_events():
    if request.method == 'GET':
        events = query_db(
            """
            SELECT ev.*, d.name as department_name, d.code as department_code
            FROM academic_events ev
            LEFT JOIN departments d ON ev.affected_department_id = d.id
            ORDER BY ev.event_date DESC
            """
        )
        return jsonify({"success": True, "events": events})

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    ev_type = data.get('event_type', 'event')
    ev_date = data.get('event_date')
    s_time = data.get('start_time', '09:00')
    e_time = data.get('end_time', '17:00')
    dept_id = data.get('affected_department_id') or None
    year = int(data.get('affected_year', 0))
    sem = int(data.get('affected_semester', 0))
    periods_lost = int(data.get('periods_lost', 0))
    desc = (data.get('description') or '').strip()

    ev_id = f"ev_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()

    query_db(
        """
        INSERT INTO academic_events (id, title, description, event_type, event_date, start_time, end_time, affected_department_id, affected_year, affected_semester, periods_lost, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ev_id, title, desc, ev_type, ev_date, s_time, e_time, dept_id, year, sem, periods_lost, now),
        commit=True
    )
    return jsonify({"success": True, "message": f"Academic event '{title}' scheduled. {periods_lost} periods recorded for recovery."})

@app.route('/api/extra-classes', methods=['GET', 'POST'])
@login_required
def api_extra_classes():
    if request.method == 'GET':
        extras = query_db(
            """
            SELECT ec.*, sub.name as subject_name, sub.code as subject_code,
                   cls.name as classroom_name, u.name as teacher_name, d.code as dept_code
            FROM extra_classes ec
            JOIN subjects sub ON ec.subject_id = sub.id
            JOIN classrooms cls ON ec.classroom_id = cls.id
            JOIN users u ON ec.teacher_id = u.id
            JOIN departments d ON ec.department_id = d.id
            ORDER BY ec.replacement_date DESC
            """
        )
        
        # Summary metrics
        total_lost = query_db("SELECT SUM(periods_lost) as s FROM academic_events", one=True)['s'] or 0
        scheduled = len(extras)
        completed = sum(1 for e in extras if e['status'] == 'completed')
        remaining = max(0, total_lost - completed)

        return jsonify({
            "success": True,
            "extra_classes": extras,
            "metrics": {
                "total_lost": total_lost,
                "replacement_scheduled": scheduled,
                "replacement_completed": completed,
                "remaining_to_recover": remaining
            }
        })

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    event_id = data.get('event_id') or None
    sub_id = data.get('subject_id')
    t_id = data.get('teacher_id')
    rep_date = data.get('replacement_date')
    period = int(data.get('period', 4))
    room_id = data.get('classroom_id')

    sub = query_db("SELECT department_id, year, semester FROM subjects WHERE id = ?", (sub_id,), one=True)
    if not sub:
        return jsonify({"success": False, "message": "Invalid subject specified."}), 400

    ext_id = f"ext_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()

    query_db(
        """
        INSERT INTO extra_classes (id, event_id, subject_id, teacher_id, department_id, year, semester, replacement_date, period, classroom_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?)
        """,
        (ext_id, event_id, sub_id, t_id, sub['department_id'], sub['year'], sub['semester'], rep_date, period, room_id, now),
        commit=True
    )
    return jsonify({"success": True, "message": "Replacement class scheduled and saved."})

@app.route('/api/extra-classes/<id>/status', methods=['PUT'])
@role_required(['admin'])
def api_toggle_extra_class(id):
    data = request.get_json() or {}
    status = data.get('status', 'completed')
    query_db("UPDATE extra_classes SET status = ? WHERE id = ?", (status, id), commit=True)
    return jsonify({"success": True, "message": f"Class status marked as {status}."})

# ==============================================================================
# Sports & Cultural Activity Periods APIs
# ==============================================================================

@app.route('/api/activities', methods=['GET', 'POST'])
@login_required
def api_activities():
    if request.method == 'GET':
        activities = query_db(
            """
            SELECT act.*, u.name as coordinator_name, d.code as department_code
            FROM activity_periods act
            LEFT JOIN users u ON act.coordinator_teacher_id = u.id
            LEFT JOIN departments d ON act.department_id = d.id
            ORDER BY act.day, act.period
            """
        )
        return jsonify({"success": True, "activities": activities})

    if session.get('role') != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    act_type = data.get('activity_type', 'sports')
    day = data.get('day', 'Wednesday')
    period = int(data.get('period', 8))
    dept_id = data.get('department_id') or None
    year = int(data.get('year', 0))
    sem = int(data.get('semester', 0))
    coord_id = data.get('coordinator_teacher_id') or None
    venue = (data.get('venue') or 'College Campus').strip()

    act_id = f"act_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()

    query_db(
        """
        INSERT INTO activity_periods (id, name, activity_type, day, period, department_id, year, semester, section, coordinator_teacher_id, venue, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'A', ?, ?, ?)
        """,
        (act_id, name, act_type, day, period, dept_id, year, sem, coord_id, venue, now),
        commit=True
    )
    return jsonify({"success": True, "message": f"Activity period '{name}' registered and protected from class collisions."})

@app.route('/api/activities/<id>', methods=['DELETE'])
@role_required(['admin'])
def api_delete_activity(id):
    query_db("DELETE FROM activity_periods WHERE id = ?", (id,), commit=True)
    return jsonify({"success": True, "message": "Activity period removed."})

# ==============================================================================
# Announcements & Notifications APIs
# ==============================================================================

@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required
def api_announcements():
    user = get_current_user()
    role = user['role']

    if request.method == 'GET':
        if role == 'student':
            ann = query_db(
                """
                SELECT * FROM announcements
                WHERE target_department = 'all'
                   OR (target_department = ? AND (target_year = ? OR target_year = 0) AND (target_semester = ? OR target_semester = 0))
                ORDER BY created_at DESC
                """,
                (user['department_id'], user['year'], user['semester'])
            )
        else:
            ann = query_db("SELECT * FROM announcements ORDER BY created_at DESC")
        return jsonify({"success": True, "announcements": ann})

    if role != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    target_dept = data.get('target_department', 'all')
    target_year = int(data.get('target_year', 0))
    target_sem = int(data.get('target_semester', 0))

    ann_id = f"ann_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()

    query_db(
        "INSERT INTO announcements (id, title, content, target_department, target_year, target_semester, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ann_id, title, content, target_dept, target_year, target_sem, now),
        commit=True
    )
    return jsonify({"success": True, "message": "Announcement broadcasted successfully."})

@app.route('/api/announcements/<id>', methods=['DELETE'])
@role_required(['admin'])
def api_delete_announcement(id):
    query_db("DELETE FROM announcements WHERE id = ?", (id,), commit=True)
    return jsonify({"success": True, "message": "Announcement deleted."})

@app.route('/api/notifications', methods=['GET'])
@login_required
def api_notifications():
    user = get_current_user()
    my_id = user['id']
    role = user['role']

    # Get specific notifications and broadcast ones
    notifs = query_db(
        """
        SELECT * FROM notifications
        WHERE user_id = ? OR user_id = 'all_students' OR (user_id = 'admin' AND ? = 'admin')
        ORDER BY created_at DESC
        LIMIT 30
        """,
        (my_id, role)
    )
    unread_count = sum(1 for n in notifs if not n['is_read'])
    return jsonify({"success": True, "notifications": notifs, "unread_count": unread_count})

@app.route('/api/notifications/<id>/read', methods=['POST'])
@login_required
def api_read_notification(id):
    query_db("UPDATE notifications SET is_read = 1 WHERE id = ?", (id,), commit=True)
    return jsonify({"success": True})

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_read():
    user = get_current_user()
    query_db("UPDATE notifications SET is_read = 1 WHERE user_id = ? OR user_id = 'all_students'", (user['id'],), commit=True)
    return jsonify({"success": True, "message": "All notifications marked as read."})

# ==============================================================================
# Application Entry Point
# ==============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print(" TimetablePro - College Timetable Automation & Management System")
    print(" Server active on http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
