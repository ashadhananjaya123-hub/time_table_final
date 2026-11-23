"""
TimetablePro - Faculty Utilization & Workload Analytics Engine
Calculates teaching periods, available institutional periods (excluding breaks/holidays),
utilization percentages, department allocations, and formats data for Chart.js.
"""

from database import query_db

# Weekly configuration: 6 working days * 8 teaching periods = 48 max slots
MAX_WEEKLY_TEACHING_PERIODS = 48

def get_faculty_workload_analytics(department_id=None, teacher_id=None):
    """
    Computes comprehensive workload statistics and Chart.js payloads.
    Excludes institutional breaks and non-teaching times from available periods.
    """
    # Base query for teachers
    teacher_sql = "SELECT id, name, department_id, email FROM users WHERE role = 'teacher'"
    teacher_params = []
    
    if department_id and department_id != 'all':
        teacher_sql += " AND department_id = ?"
        teacher_params.append(department_id)
        
    if teacher_id and teacher_id != 'all':
        teacher_sql += " AND id = ?"
        teacher_params.append(teacher_id)
        
    teachers = query_db(teacher_sql, teacher_params)
    departments = {d['id']: d for d in query_db("SELECT id, name, code FROM departments")}
    
    # Count assigned slots for each teacher from active timetable_slots
    assigned_slots = query_db(
        """
        SELECT ts.teacher_id, ts.day, ts.period, ts.slot_type, sub.name as sub_name, sub.type as sub_type
        FROM timetable_slots ts
        JOIN timetables t ON ts.timetable_id = t.id
        LEFT JOIN subjects sub ON ts.subject_id = sub.id
        WHERE ts.teacher_id IS NOT NULL AND ts.slot_type != 'activity'
        """
    )
    
    # Map slots by teacher
    teacher_slot_map = {t['id']: [] for t in teachers}
    for s in assigned_slots:
        if s['teacher_id'] in teacher_slot_map:
            teacher_slot_map[s['teacher_id']].append(s)

    faculty_metrics = []
    
    high_workload_threshold = 16 # periods/week
    low_workload_threshold = 8   # periods/week
    
    # Available teaching periods per week per teacher
    # Standard 48 periods per week (breaks are already between periods, not counted)
    available_periods = MAX_WEEKLY_TEACHING_PERIODS

    for t in teachers:
        slots = teacher_slot_map[t['id']]
        assigned_count = len(slots)
        utilization_pct = round((assigned_count / available_periods) * 100, 1) if available_periods > 0 else 0
        
        dept = departments.get(t['department_id'], {"code": "GEN", "name": "General"})
        
        status = "normal"
        if assigned_count >= high_workload_threshold:
            status = "high"
        elif assigned_count <= low_workload_threshold:
            status = "low"
            
        faculty_metrics.append({
            "teacher_id": t['id'],
            "name": t['name'],
            "department_code": dept['code'],
            "department_name": dept['name'],
            "assigned_periods": assigned_count,
            "available_periods": available_periods,
            "utilization_pct": utilization_pct,
            "status": status,
            "slots": slots
        })
        
    # Sort by utilization descending
    faculty_metrics.sort(key=lambda x: x['assigned_periods'], reverse=True)

    # 1. Bar Chart Data: Teacher vs Assigned Periods
    bar_labels = [f['name'].replace('Prof. ', '').replace('Dr. ', '') for f in faculty_metrics[:10]]
    bar_assigned = [f['assigned_periods'] for f in faculty_metrics[:10]]
    bar_available = [f['available_periods'] for f in faculty_metrics[:10]]
    
    # 2. Doughnut Chart Data: Department Workload Share
    dept_tally = {}
    for f in faculty_metrics:
        code = f['department_code']
        dept_tally[code] = dept_tally.get(code, 0) + f['assigned_periods']
        
    doughnut_labels = list(dept_tally.keys())
    doughnut_values = list(dept_tally.values())

    # 3. Line Chart Data: Weekly Load Trend by Day (Mon-Sat)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    day_tally = {d: 0 for d in days}
    for s in assigned_slots:
        if s['day'] in day_tally:
            day_tally[s['day']] += 1
            
    line_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    line_values = [day_tally[d] for d in days]

    # Summary Statistics
    total_assigned = sum(f['assigned_periods'] for f in faculty_metrics)
    avg_utilization = round(sum(f['utilization_pct'] for f in faculty_metrics) / len(faculty_metrics), 1) if faculty_metrics else 0
    high_workload_count = sum(1 for f in faculty_metrics if f['status'] == 'high')
    low_workload_count = sum(1 for f in faculty_metrics if f['status'] == 'low')

    return {
        "faculty_metrics": faculty_metrics,
        "summary": {
            "total_faculty": len(faculty_metrics),
            "total_assigned_periods": total_assigned,
            "average_utilization_pct": avg_utilization,
            "high_workload_count": high_workload_count,
            "low_workload_count": low_workload_count
        },
        "charts": {
            "bar": {
                "labels": bar_labels,
                "assigned": bar_assigned,
                "available": bar_available
            },
            "doughnut": {
                "labels": doughnut_labels,
                "values": doughnut_values
            },
            "line": {
                "labels": line_labels,
                "values": line_values
            }
        }
    }
