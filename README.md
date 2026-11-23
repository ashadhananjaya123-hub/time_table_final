# TimetablePro: Modern Automated Class Timetable & Academic Management System

A full-stack, responsive college timetable automation and academic scheduling platform built with **Python Flask**, **MySQL / SQLite**, **HTML5/CSS3/JavaScript**, **Bootstrap 5**, **Chart.js**, **FullCalendar**, and **Lucide Icons**.

Developed following a clean **SaaS Light Theme**, **Balanced Bento Grid Layout**, and an **Indigo Accent (`#4f46e5`)** with a strict university design standard (clean SVG Lucide icons with zero decorative emojis).

---

## 1. System Overview & Objectives

Academic timetable coordination is a complex constraint satisfaction problem. **TimetablePro** automates scheduling across academic departments, instructors, classrooms, and student cohorts, while integrating institutional academic operations:

1. **Automated Timetable Generation**: Conflict-free 6-day (Monday to Saturday, 8 periods/day) schedule generation with lab block pairing and activity period protection.
2. **Mutual Teacher-to-Teacher Class Swapping**: Peer-to-peer exchange workflow where mutual consent automatically commits timetable adjustments without requiring routine administrative approvals.
3. **Faculty Workload & Utilization Analytics**: Dedicated Chart.js visualizations (bar, doughnut, line trend) calculating actual teaching periods vs available institutional periods (excluding breaks/holidays).
4. **Institutional Master & Personal Calendars**: FullCalendar integration (Day, Week, Month views) aggregating classes, workshops, holidays, extra recovery classes, and activity periods.
5. **Teacher Academic Progress Tracking**: Syllabus topic completion tracking with dates and teaching notes, alongside coursework assignment issuance and student submission tracking.
6. **Events & Lost-Class Recovery Dashboard**: Log disruptions from seminars and workshops, calculate periods lost, and allocate conflict-checked replacement teaching hours.
7. **Protected Sports & Cultural Activity Periods**: Configurable non-academic routines that the timetable engine guarantees will never be scheduled over with regular lectures.
8. **Student Portal & Faculty Directory Search**: Cohort-scoped daily and weekly routines, printer-optimized timetable view, and live searchable faculty directory.

---

## 2. Technology Stack

- **Frontend**:
  - HTML5 & CSS3 (Custom SaaS Bento Grid System)
  - Bootstrap 5.3.3 (Responsive Grid & Modals)
  - Lucide Icons (Professional Vector Icons, Zero Emojis)
  - Chart.js 4 (Workload Comparison & Department Allocation Visuals)
  - FullCalendar 6.1.15 (Day, Week, Month Interactive Calendar)
- **Backend**:
  - Python 3 (Flask 3.1)
  - Secure Session Management & Password Hashing (`werkzeug.security`)
  - Role-Based Access Control (`@login_required`, `@role_required`)
- **Database Engine**:
  - **Dual Database Architecture**:
    - **SQLite (Default Out-of-the-Box)**: Pre-configured in `timetable.db` with zero external setup needed for immediate execution.
    - **MySQL (Production Ready)**: Fully supported via `config.py` and provided `schema_mysql.sql` for institutional deployment.

---

## 3. Folder Structure

```
timetable/
├── app.py                      # Flask Application Controller, Routes & REST APIs
├── config.py                   # App Configuration (SQLite / MySQL Dual Mode)
├── database.py                 # Database Layer, Schema Creation & Data Seeder
├── scheduler.py                # Automatic Timetable CSP Generator & Validator
├── swap_manager.py             # Mutual Teacher Swapping & Atomic Commit Engine
├── analytics.py                # Faculty Utilization & Chart.js Metrics Engine
├── schema_mysql.sql            # MySQL Database DDL Script for Production
├── requirements.txt            # Python Dependencies
├── timetable.db                # SQLite Local Database (Auto-initialized with seed data)
├── README.md                   # Complete Documentation
├── static/
│   ├── css/
│   │   └── style.css           # Bento Grid SaaS Theme, Indigo Accent, Print Styles
│   └── js/
│       ├── main.js             # Global Shell, Notifications, Toasts, Lucide Init
│       ├── admin.js            # Admin Dashboard, Charts, CRUD, Slot Editor, Recovery
│       ├── teacher.js          # Teacher Dashboard, Swaps Hub, Syllabus, Assignments
│       └── student.js          # Student Portal, Routine, Timetable, Teacher Search
└── templates/
    ├── base.html               # Common Layout, Sidebar, Topbar, Drawers
    ├── login.html              # Modern SaaS Login Screen with Role Switcher
    ├── admin.html              # Administrator Control Center (Bento Sections)
    ├── teacher.html            # Faculty Instruction & Coordination Portal
    └── student.html            # Student Academic Schedule & Routine Portal
```

---

## 4. Demonstration Login Credentials

The application is pre-seeded with active demonstration accounts. On the login page (`/login`), click any of the **Quick Demo Credentials** pills for 1-click auto-fill:

| Role | Username | Password | Profile Description |
|------|----------|----------|---------------------|
| **Administrator** | `admin` | `admin123` | Master control over faculty, students, timetables, and facilities |
| **Faculty (Teacher)** | `rajesh` | `teacher123` | Dr. Rajesh Kumar (CSE Department, Data Structures) |
| **Faculty (Teacher)** | `sneha` | `teacher123` | Prof. Sneha Iyer (CSE Department, Digital Logic Design) |
| **Faculty (Teacher)** | `vikram` | `teacher123` | Dr. Vikram Singh (ECE Department, Signals & Systems) |
| **Student** | `amit` | `student123` | Amit Sharma (CSE, Year 1, Semester 1, Section A) |
| **Student** | `rahul` | `student123` | Rahul Verma (CSE, Year 1, Semester 2, Section A) |
| **Student** | `deepa` | `student123` | Deepa Menon (ECE, Year 2, Semester 3, Section A) |

---

## 5. How to Run the Website

### Step 1: Ensure Python is Installed
Verify Python 3 is available:
```powershell
python --version
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```
*(Dependencies: `flask`, `werkzeug`, `pymysql`, `cryptography`)*

### Step 3: Start the Application
Run the Flask server from the project directory:
```powershell
python app.py
```

### Step 4: Access in Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
The database will automatically initialize `timetable.db` with sample records on first run.

---

## 6. Switching to MySQL (Optional Production Mode)

If you prefer to connect to an external MySQL server:

1. Import the provided schema:
   ```bash
   mysql -u root -p < schema_mysql.sql
   ```
2. Configure your environment variables or update `config.py`:
   ```python
   DB_TYPE = 'mysql'
   MYSQL_HOST = 'localhost'
   MYSQL_PORT = 3306
   MYSQL_USER = 'root'
   MYSQL_PASSWORD = 'your_password'
   MYSQL_DB = 'timetablepro'
   ```
3. Restart `app.py`. The application will connect directly to MySQL.

---

## 7. Deep-Dive Feature Implementations

### A. Automatic Timetable Generation Algorithm (`scheduler.py`)
- **Greedy Constraint Satisfaction Algorithm with Stochastic Backtracking**:
  - **Lab Unit Priority**: Laboratory courses occupy contiguous 2-period afternoon blocks (Periods 6–7 or 7–8) assigned strictly to `lab` type facilities.
  - **Balanced Theory Distribution**: Theory courses are spread across weekdays (maximum 1–2 hours per subject/day) to prevent student and faculty fatigue.
  - **Protected Activity Periods**: Preserves configured sports, cultural, and club activity periods from class collisions.
  - **Inter-Cohort Collision Prevention**: Active timetables for other cohorts are indexed to prevent shared instructors or shared facilities from colliding.
  - **Diagnostic Reporting**: Returns actionable error guidance if constraints cannot be resolved.

### B. Teacher-to-Teacher Mutual Class Swapping (`swap_manager.py`)
- **Peer-to-Peer Workflow Without Routine Admin Approval**:
  1. Teacher A selects their class slot and targets a class from Teacher B.
  2. Teacher A provides an exchange justification reason.
  3. Teacher B receives an instant in-app notification.
  4. Teacher B reviews the proposal and accepts or declines.
  5. If Teacher B accepts, the system runs multi-point conflict validation (teacher availability, room availability, cohort overlaps).
  6. Upon passing, the system executes an atomic transaction updating the live timetable.
  7. Notifications are sent to both teachers, and the Administrator is notified with an entry logged in the immutable `swap_history` audit trail.

### C. Faculty Workload & Utilization Analytics (`analytics.py`)
- Real-time calculations:
  - **Teaching Periods Assigned**: Count of weekly periods teaching regular and laboratory courses.
  - **Available Teaching Periods**: 48 periods per week (6 days × 8 periods), excluding institutional breaks.
  - **Utilization Rate**: `(Assigned / Available) × 100%`.
  - **Status Categories**: Optimal, High Workload (> 65% / 16 hrs), and Light Workload (< 25% / 8 hrs).
  - Visualized using Chart.js bar and doughnut charts with dynamic department and faculty filters.

### D. Events & Lost-Class Recovery Module
- Log institutional disruptions (seminars, workshops, holidays) with affected departments and calculated periods lost.
- **Extra Teaching-Hour Allocation**: Administrators allocate replacement classes on designated dates and periods.
- Full collision checks are enforced on extra classes to ensure rooms and teachers are free.
- **Lost-Class Recovery Dashboard**: Displays total periods lost, replacement classes scheduled, completed classes, and remaining periods to recover.

### E. Teacher Academic Progress
- **Syllabus Tracking**: Instructors add syllabus topics, mark topics completed with teaching dates and notes, and track progress percentage.
- **Coursework Assignments**: Instructors publish assignments with due dates and descriptions, monitor student submission rates, and record grades.
- **Student Submission**: Students view active assignments and submit work directly with submission notes.

### F. Master & Personal Calendars
- Powered by **FullCalendar 6** with Day, Week, and Month views.
- Color-coded badges for regular lectures (Indigo), laboratories (Emerald Green), workshops (Amber), holidays (Crimson), extra recovery classes (Purple), and activities (Forest Green).

---

## 8. Test Verification Results

All three roles and modules have been verified:

- [x] **Authentication & Guarding**: Tested login with Admin, Teacher, and Student credentials. Unauthorized route access redirected.
- [x] **Timetable Generation**: Successfully generated and validated timetables for CSE Year 1 Semester 1 and Semester 2 with 0 constraint collisions.
- [x] **Interactive Slot Editor**: Verified slot re-assignment and clearing to free periods.
- [x] **Mutual Swaps**: Executed peer swap between Dr. Rajesh Kumar (`tch_1`) and Prof. Sneha Iyer (`tch_2`); verified atomic timetable update and administrator notification.
- [x] **Workload Analytics**: Verified Chart.js bar and doughnut visualizations reflecting real-time timetable changes.
- [x] **Lost-Class Recovery**: Scheduled replacement extra class linked to symposium event disruption; tracked recovery completion.
- [x] **Syllabus Progress**: Verified topic completion checkboxes updating progress percentages in real-time.
- [x] **Assignment Submissions**: Student submitted coursework assignment; faculty viewed submission status.
- [x] **Design Compliance**: Confirmed light SaaS Bento Grid layout, indigo accent, and zero decorative emojis (strictly Lucide icons).
#   t i m e t a b l e p r o  
 #   t i m e _ t a b l e _ f i n a l  
 "# time_table_final" 
"# time_table_final" 
