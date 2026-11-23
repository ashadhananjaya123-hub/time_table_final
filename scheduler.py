"""
TimetablePro - Automatic Timetable Generation & Constraint Satisfaction Engine
Implements CSP with greedy heuristic backtracking.
Enforces Hard & Soft constraints, lab block pairing, activity period protection,
and inter-timetable resource conflict prevention.
"""

import random
import datetime
from database import query_db

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

PERIODS = [
    {"number": 1, "start": "08:30", "end": "09:30", "type": "class"},
    {"number": 2, "start": "09:30", "end": "10:30", "type": "class"},
    {"number": 3, "start": "10:45", "end": "11:45", "type": "class"},
    {"number": 4, "start": "11:45", "end": "12:45", "type": "class"},
    {"number": 5, "start": "01:30", "end": "02:30", "type": "class"},
    {"number": 6, "start": "02:30", "end": "03:30", "type": "class"},
    {"number": 7, "start": "03:30", "end": "04:30", "type": "class"},
    {"number": 8, "start": "04:30", "end": "05:15", "type": "class"}
]

def get_periods_config():
    return PERIODS

def get_days_config():
    return DAYS

def validate_timetable_slots(slots, exclude_timetable_id=None):
    """
    Validates a list of timetable slots against all hard constraints,
    checking internal cohort collisions as well as external collisions
    with other active timetables in the database.
    """
    conflicts = []
    
    cohort_time_map = {}
    teacher_time_map = {}
    room_time_map = {}
    
    # Check internal consistency
    for s in slots:
        day = s.get('day')
        period = int(s.get('period'))
        teacher_id = s.get('teacher_id')
        room_id = s.get('classroom_id')
        slot_type = s.get('slot_type', 'regular')
        
        time_key = f"{day}_{period}"
        
        # 1. Cohort collision
        if time_key in cohort_time_map:
            conflicts.append(f"Cohort double-booked on {day} Period {period}.")
        else:
            cohort_time_map[time_key] = s
            
        # 2. Teacher internal collision
        if teacher_id:
            t_key = f"{teacher_id}_{time_key}"
            if t_key in teacher_time_map:
                conflicts.append(f"Teacher {teacher_id} assigned multiple classes on {day} Period {period}.")
            else:
                teacher_time_map[t_key] = s
                
        # 3. Room internal collision
        if room_id:
            r_key = f"{room_id}_{time_key}"
            if r_key in room_time_map:
                conflicts.append(f"Classroom/Lab {room_id} double-booked on {day} Period {period}.")
            else:
                room_time_map[r_key] = s

    # Check external collisions against all other active timetables
    sql = """
        SELECT ts.day, ts.period, ts.teacher_id, ts.classroom_id, t.id as tt_id,
               d.code as dept_code, t.year, t.semester, t.section,
               u.name as teacher_name, cls.name as classroom_name
        FROM timetable_slots ts
        JOIN timetables t ON ts.timetable_id = t.id
        JOIN departments d ON t.department_id = d.id
        LEFT JOIN users u ON ts.teacher_id = u.id
        LEFT JOIN classrooms cls ON ts.classroom_id = cls.id
    """
    params = []
    if exclude_timetable_id:
        sql += " WHERE t.id != ?"
        params.append(exclude_timetable_id)
        # Also exclude legacy ID without section suffix if applicable
        legacy_id = exclude_timetable_id.rsplit('_', 1)[0]
        sec_id = f"{exclude_timetable_id}_A"
        sql += " AND t.id != ? AND t.id != ?"
        params.extend([legacy_id, sec_id])
        
    other_slots = query_db(sql, params)
    
    for os in other_slots:
        o_day = os['day']
        o_period = os['period']
        o_teacher = os['teacher_id']
        o_room = os['classroom_id']
        t_name = os.get('teacher_name') or os['teacher_id']
        r_name = os.get('classroom_name') or os['classroom_id']
        cohort_label = f"{os['dept_code']} Y{os['year']} S{os['semester']} Sec {os.get('section') or 'A'}"
        
        for s in slots:
            if s.get('day') == o_day and int(s.get('period')) == o_period:
                if s.get('teacher_id') and s.get('teacher_id') == o_teacher:
                    conflicts.append(f"External Teacher Collision: Faculty '{t_name}' is already teaching in {cohort_label} on {o_day} Period {o_period}.")
                if s.get('classroom_id') and s.get('classroom_id') == o_room:
                    conflicts.append(f"External Room Collision: Facility '{r_name}' is occupied by {cohort_label} on {o_day} Period {o_period}.")

    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts
    }

def generate_timetable(department_id, year, semester, section="A"):
    """
    Generates a full 6-day academic timetable honoring theory & lab requirements,
    protected activity periods, room capabilities, and teacher availability.
    """
    y = int(year)
    s = int(semester)
    
    # 1. Fetch subjects
    subjects = query_db(
        "SELECT * FROM subjects WHERE department_id = ? AND year = ? AND semester = ?",
        (department_id, y, s)
    )
    if not subjects:
        return {
            "success": False,
            "errors": [f"No curriculum subjects found for selected Department, Year {y}, Semester {s}."]
        }
        
    # Check that subjects have assigned teachers
    for sub in subjects:
        if not sub.get('teacher_id'):
            return {
                "success": False,
                "errors": [f"Subject '{sub['name']}' ({sub['code']}) has no assigned instructor. Assign faculty first."]
            }
            
    # 2. Fetch facilities
    all_rooms = query_db("SELECT * FROM classrooms")
    theory_rooms = [r for r in all_rooms if r['type'] == 'classroom']
    lab_rooms = [r for r in all_rooms if r['type'] == 'lab']
    
    if not theory_rooms:
        return {"success": False, "errors": ["No lecture classrooms available in the facility database."]}
        
    has_labs = any(sub['type'] == 'lab' for sub in subjects)
    if has_labs and not lab_rooms:
        return {"success": False, "errors": ["Laboratory subjects exist, but no laboratory facilities are configured."]}
        
    # 3. Check protected activity periods
    activities = query_db(
        "SELECT * FROM activity_periods WHERE (department_id = ? OR department_id IS NULL) AND (year = ? OR year = 0) AND (semester = ? OR semester = 0)",
        (department_id, y, s)
    )
    protected_activity_slots = {}
    for act in activities:
        protected_activity_slots[(act['day'], act['period'])] = act

    # 4. Fetch busy slots from other existing timetables
    sec = section or 'A'
    current_tt_id = f"tt_{department_id}_{y}_{s}_{sec}"
    external_slots = query_db(
        """
        SELECT ts.day, ts.period, ts.teacher_id, ts.classroom_id
        FROM timetable_slots ts
        JOIN timetables t ON ts.timetable_id = t.id
        WHERE t.id != ? AND t.id != ?
        """,
        (current_tt_id, f"tt_{department_id}_{y}_{s}")
    )
    
    reserved_teachers = set()
    reserved_rooms = set()
    for es in external_slots:
        reserved_teachers.add(f"{es['teacher_id']}_{es['day']}_{es['period']}")
        reserved_rooms.add(f"{es['classroom_id']}_{es['day']}_{es['period']}")

    # 5. Stochastic Constraint Satisfaction Generator Loop
    max_attempts = 60
    best_slots = None
    
    for attempt in range(max_attempts):
        grid = {} # (day, period) -> slot dict
        
        attempt_teachers_busy = set(reserved_teachers)
        attempt_rooms_busy = set(reserved_rooms)
        
        # Lock in protected activity periods
        for (act_day, act_period), act in protected_activity_slots.items():
            grid[(act_day, act_period)] = {
                "day": act_day,
                "period": act_period,
                "subject_id": None,
                "teacher_id": act.get('coordinator_teacher_id'),
                "classroom_id": None,
                "slot_type": "activity"
            }
            if act.get('coordinator_teacher_id'):
                attempt_teachers_busy.add(f"{act['coordinator_teacher_id']}_{act_day}_{act_period}")

        # Separate subject units into Labs and Theory
        lab_units = []
        theory_units = []
        
        for sub in subjects:
            hours = int(sub.get('hours_per_week', 4))
            if sub['type'] == 'lab':
                # Labs require 2 consecutive periods
                pairs = hours // 2
                for _ in range(pairs):
                    lab_units.append({"subject": sub, "duration": 2})
                if hours % 2 != 0:
                    lab_units.append({"subject": sub, "duration": 1})
            else:
                for _ in range(hours):
                    theory_units.append({"subject": sub, "duration": 1})

        # Shuffle units for stochastic distribution
        random.shuffle(lab_units)
        random.shuffle(theory_units)
        
        failed = False
        
        # A. Place Lab Units First (Preferred in Afternoon: Periods 6-7 or 7-8)
        lab_candidate_periods = [(6, 7), (7, 8), (4, 5), (1, 2)]
        shuffled_days = list(DAYS)
        random.shuffle(shuffled_days)
        
        for unit in lab_units:
            placed = False
            for d in shuffled_days:
                if placed:
                    break
                for p1, p2 in lab_candidate_periods:
                    # Check cohort slots free
                    if (d, p1) in grid or (d, p2) in grid:
                        continue
                    
                    t_id = unit['subject']['teacher_id']
                    t_key1 = f"{t_id}_{d}_{p1}"
                    t_key2 = f"{t_id}_{d}_{p2}"
                    if t_key1 in attempt_teachers_busy or t_key2 in attempt_teachers_busy:
                        continue
                        
                    # Find free lab room
                    available_lab = None
                    shuffled_labs = list(lab_rooms)
                    random.shuffle(shuffled_labs)
                    for r in shuffled_labs:
                        r_key1 = f"{r['id']}_{d}_{p1}"
                        r_key2 = f"{r['id']}_{d}_{p2}"
                        if r_key1 not in attempt_rooms_busy and r_key2 not in attempt_rooms_busy:
                            available_lab = r
                            break
                            
                    if available_lab:
                        # Place lab in both consecutive periods
                        for p in (p1, p2):
                            grid[(d, p)] = {
                                "day": d,
                                "period": p,
                                "subject_id": unit['subject']['id'],
                                "teacher_id": t_id,
                                "classroom_id": available_lab['id'],
                                "slot_type": "lab"
                            }
                            attempt_teachers_busy.add(f"{t_id}_{d}_{p}")
                            attempt_rooms_busy.add(f"{available_lab['id']}_{d}_{p}")
                        placed = True
                        break
            if not placed:
                failed = True
                break
                
        if failed:
            continue
            
        # B. Place Theory Units
        # Balance subjects so the same subject doesn't appear > 2 times per day
        subject_day_tally = {sub['id']: {d: 0 for d in DAYS} for sub in subjects}
        
        for unit in theory_units:
            sub = unit['subject']
            t_id = sub['teacher_id']
            placed = False
            
            # Sort days by least count for this subject
            candidate_days = sorted(DAYS, key=lambda d: (subject_day_tally[sub['id']][d], random.random()))
            
            for d in candidate_days:
                if placed:
                    break
                if subject_day_tally[sub['id']][d] >= 2:
                    continue
                    
                # Prefer periods 1 through 5, then 6 to 8
                period_order = [1, 2, 3, 4, 5, 6, 7, 8]
                random.shuffle(period_order)
                
                for p in period_order:
                    if (d, p) in grid:
                        continue
                        
                    t_key = f"{t_id}_{d}_{p}"
                    if t_key in attempt_teachers_busy:
                        continue
                        
                    # Find free theory classroom
                    available_room = None
                    shuffled_rooms = list(theory_rooms)
                    random.shuffle(shuffled_rooms)
                    for r in shuffled_rooms:
                        r_key = f"{r['id']}_{d}_{p}"
                        if r_key not in attempt_rooms_busy:
                            available_room = r
                            break
                            
                    if available_room:
                        grid[(d, p)] = {
                            "day": d,
                            "period": p,
                            "subject_id": sub['id'],
                            "teacher_id": t_id,
                            "classroom_id": available_room['id'],
                            "slot_type": "regular"
                        }
                        attempt_teachers_busy.add(t_key)
                        attempt_rooms_busy.add(f"{available_room['id']}_{d}_{p}")
                        subject_day_tally[sub['id']][d] += 1
                        placed = True
                        break
                        
            if not placed:
                failed = True
                break
                
        if not failed:
            # Succeeded!
            best_slots = list(grid.values())
            break
            
    if not best_slots:
        return {
            "success": False,
            "errors": [
                "Constraint Bottleneck: Unable to find a collision-free timetable allocation.",
                "Potential causes: High faculty scheduling overlap across cohorts, insufficient classrooms or laboratories, or dense curriculum hours.",
                "Recommendation: Verify that instructors are not over-committed across multiple departments at the same periods."
            ]
        }
        
    # Final verification
    validation = validate_timetable_slots(best_slots, exclude_timetable_id=current_tt_id)
    if not validation['valid']:
        return {
            "success": False,
            "errors": ["Generation resulted in unresolved collisions: " + "; ".join(validation['conflicts'])]
        }
        
    return {
        "success": True,
        "slots": best_slots,
        "timetable_id": current_tt_id
    }
