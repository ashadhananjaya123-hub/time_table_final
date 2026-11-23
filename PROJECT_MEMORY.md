# TimetablePro: Complete Project Memory & Implementation Record

**Project**: Automated Class Timetable Generation and Management System  
**Course Context**: College 5th Semester Software Engineering Project  
**Repository Working Directory**: `d:\Desktop\5th\software project\timetable`  
**GitHub Repository**: `https://github.com/ashadhananjaya123-hub/timetablepro.git` (branch: `main` - synchronized)  
**Last Updated**: November 22, 2026  

---

## 1. Core Architectural Overview

TimetablePro is a full-stack, responsive academic scheduling web application engineered with:
- **Backend**: Python 3 (Flask 3.1) with modular separation of concerns.
- **Frontend**: Custom SaaS Bento Grid (CSS3), Bootstrap 5.3.3, Lucide Icons, Chart.js 4, and FullCalendar 6.1.15.
- **Database Engine**: Dual-mode architecture:
  - **SQLite (`timetable.db`)**: Pre-seeded local SQLite database for instant, zero-configuration out-of-the-box execution.
  - **MySQL (`schema_mysql.sql`)**: Production-ready InnoDB script with strict foreign keys, cascade constraints, and query indexes. Configurable via `config.py`.
- **Security & RBAC**:
  - Secure session cookies (`HttpOnly`, `SameSite=Lax`).
  - One-way password hashing via `werkzeug.security.generate_password_hash` / `check_password_hash`.
  - Route decorators: `@login_required` and `@role_required(['admin', 'teacher', 'student'])`.
- **Hosting & Deployment Ready**:
  - `wsgi.py`: WSGI entrypoint for Gunicorn / uWSGI / cloud deployment.
  - `Procfile`: Gunicorn web worker definition (`web: gunicorn wsgi:app`).
  - `render.yaml`: Infrastructure-as-code blueprint for Render.com deployment.
  - `requirements.txt`: Includes `flask`, `werkzeug`, `pymysql`, `cryptography`, and `gunicorn`.
  - `.gitignore`: Configured to avoid committing caches, temp files, and credentials.
  - GitHub remote configured and pushed to `main` branch.

---

## 2. Design System & User Interface Constraints

- **Theme**: Clean Light SaaS Theme.
- **Layout**: Balanced Bento Grid (`.bento-grid`, `.bento-card`).
- **Accent Colour**: Indigo (`#4f46e5`, hover `#4338ca`).
- **Typography**: Modern, legible system sans-serif hierarchy (`Inter`, `-apple-system`, `Segoe UI`, Roboto).
- **EMOJI RESTRICTION (STRICT)**: Zero decorative emojis anywhere in HTML, CSS, JavaScript, or backend templates. Every icon is a clean, scalable vector SVG from **Lucide Icons** (`<i data-lucide="..."></i>`).
- **Visual Balance**: Neutral borders (`#e2e8f0`), subtle drop shadows (`0 1px 3px rgba(0,0,0,0.05)`), light slate backgrounds (`#f8fafc`), and colored badge pills for status indicators.
- **Width Customization**:
  - Mutual class swap modal (`#modalInitiateSwap`) is expanded width-wise to **960px** (`modal-xl`, `width: 92%`) with a 2-column layout (Offer vs Receive) to comfortably fit long class titles and room strings.
  - Dashboard card is expanded to `col-span-6` (50% desktop grid width).
  - Swap tables use `.swap-table-wide` (`min-width: 900px`) with expanded justification reason cells (`min-width: 200px; max-width: 380px;`).
  - **All font sizes remain strictly unchanged** (`1rem` titles, `0.8rem` labels, `0.85rem`/`0.825rem` table text).

---

## 3. Database Schema & Models (`database.py` / `schema_mysql.sql`)

The system manages 16 interconnected relational entities:
1. `departments` (`id`, `name`, `code`, `created_at`)
2. `classrooms` (`id`, `name`, `type`, `capacity`, `building`) - Supports `classroom` and `lab` types.
3. `users` (`id`, `username`, `password_hash`, `role`, `name`, `email`, `phone`, `department_id`, `roll_no`, `year`, `semester`, `section`, `created_at`)
4. `academic_cohorts` (`id`, `department_id`, `year`, `semester`, `section`)
5. `subjects` (`id`, `name`, `code`, `department_id`, `year`, `semester`, `type`, `hours_per_week`, `teacher_id`)
6. `timetables` (`id`, `department_id`, `year`, `semester`, `section`, `published`, `generated_at`, `updated_at`)
7. `timetable_slots` (`id`, `timetable_id`, `day`, `period`, `subject_id`, `teacher_id`, `classroom_id`, `slot_type`)
8. `swap_requests` (`id`, `sender_teacher_id`, `receiver_teacher_id`, `sender_day`, `sender_period`, `sender_subject_id`, `receiver_day`, `receiver_period`, `receiver_subject_id`, `reason`, `status`, `admin_notified`, `created_at`, `updated_at`)
9. `swap_history` (`id`, `swap_request_id`, `sender_name`, `receiver_name`, `details`, `executed_at`) - Immutable audit log.
10. `events` (`id`, `title`, `event_type`, `department_id`, `start_date`, `end_date`, `start_period`, `end_period`, `description`, `lost_hours`, `created_at`)
11. `extra_classes` (`id`, `event_id`, `department_id`, `year`, `semester`, `section`, `subject_id`, `teacher_id`, `classroom_id`, `scheduled_date`, `period`, `status`, `notes`, `created_at`)
12. `activity_periods` (`id`, `name`, `activity_type`, `day`, `period`, `department_id`, `year`, `semester`, `section`, `coordinator_teacher_id`, `venue`, `created_at`) - Protected sports and cultural blocks.
13. `syllabus_topics` (`id`, `subject_id`, `unit_number`, `title`, `description`, `estimated_hours`, `is_completed`, `completed_at`, `teaching_notes`)
14. `assignments` (`id`, `subject_id`, `teacher_id`, `title`, `description`, `due_date`, `max_marks`, `created_at`)
15. `assignment_submissions` (`id`, `assignment_id`, `student_id`, `submitted_at`, `submission_text`, `grade`, `feedback`)
16. `notifications` (`id`, `user_id`, `user_role`, `title`, `message`, `link`, `is_read`, `created_at`)

---

## 4. Key Subsystem Implementations

### A. Automatic Timetable Generation Algorithm (`scheduler.py`)
- **Stochastic Greedy CSP Engine**:
  - Generates 6-day routines (Monday to Saturday) across 8 daily periods.
  - **Lab Unit Priority**: Laboratory courses are split into contiguous 2-period afternoon blocks (Periods 6–7 or 7–8) assigned strictly to `lab` type facilities.
  - **Theory Balancing**: Lectures are distributed evenly across weekdays (max 1–2 hours per subject/day) to prevent cognitive overload.
  - **Protected Activity Locks**: Pre-populates configured sports/cultural periods and guarantees zero class scheduling overlaps.
  - **Cross-Cohort Collision Prevention**: Gathers occupied slots across all other departmental timetables to prevent teacher or classroom conflicts.
  - **Conflict Validator (`validate_timetable_slots`)**: Enforces zero double-booking on teacher IDs, classroom IDs, and cohort time slots.

### B. Mutual Teacher-to-Teacher Class Swapping (`swap_manager.py`)
- **Peer-to-Peer Workflow Without Admin Gatekeeping**:
  - Teacher A initiates a swap request targeting Teacher B's specific slot with a stated justification.
  - Teacher B receives an in-app notification and reviews the proposal.
  - Upon acceptance, multi-point collision checks verify that Teacher A is not busy at Teacher B's time and Teacher B is not busy at Teacher A's time.
  - Timetable slots are atomically updated in the database.
  - Notifications are dispatched to both teachers and the Administrator; details are recorded into `swap_history`.

### C. Faculty Workload & Utilization Analytics (`analytics.py`)
- Real-time calculations:
  - **Assigned Teaching Hours**: Sum of assigned theory and lab periods per week.
  - **Available Teaching Periods**: 48 periods per week (6 days × 8 periods), excluding breaks and holidays.
  - **Utilization Rate**: `(Assigned / Available) × 100%`.
  - **Workload Statuses**: Optimal (25–65%), High Workload (>65% / 16 hrs), Light Workload (<25% / 8 hrs).
  - Formats data payloads for Chart.js horizontal bar charts and departmental doughnut charts.

### D. Events & Lost-Class Recovery
- Logs disruptions (seminars, workshops, symposiums) and calculates lost lecture hours.
- Admin allocates collision-checked replacement extra classes on designated dates and periods.
- Tracks recovery progress metrics (total lost, scheduled, completed, remaining).

### E. Academic Progress & Coursework
- **Syllabus Tracker**: Topic-level completion checkboxes with completion dates and instructor notes; computes syllabus completion percentage.
- **Assignments**: Instructors publish coursework with deadlines; students submit notes/links; instructors track submission status.

### F. Master & Personal Calendars
- Powered by FullCalendar 6 with Day, Week, and Month views.
- Color codes events: Regular classes (Indigo), Labs (Emerald), Workshops (Amber), Holidays (Crimson), Extra classes (Purple), Activities (Forest Green).

---

## 5. Demonstration Accounts

| Role | Username | Password | Details |
|------|----------|----------|---------|
| **Administrator** | `admin` | `admin123` | Complete institutional control |
| **Faculty** | `rajesh` | `teacher123` | Dr. Rajesh Kumar (CSE - Data Structures) |
| **Faculty** | `sneha` | `teacher123` | Prof. Sneha Iyer (CSE - Digital Logic Design) |
| **Faculty** | `vikram` | `teacher123` | Dr. Vikram Singh (ECE - Signals & Systems) |
| **Student** | `amit` | `student123` | Amit Sharma (CSE Y1S1 Sec A) |
| **Student** | `rahul` | `student123` | Rahul Verma (CSE Y1S2 Sec A) |
| **Student** | `deepa` | `student123` | Deepa Menon (ECE Y2S3 Sec A) |

---

## 6. Verification Status & Git Status

- **Automated Tests**: All 8 tests in `test_suite.py` pass cleanly (100% pass rate).
- **Emoji Audit**: Zero decorative emojis across all HTML, CSS, JavaScript, and Python files.
- **Git Repository Status**: Pushed and up-to-date with remote `origin/main` at `https://github.com/ashadhananjaya123-hub/timetablepro.git`.
