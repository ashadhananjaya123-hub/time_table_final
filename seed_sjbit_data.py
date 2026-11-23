"""
Script to seed all 33 SJBIT CSE faculty members, their subjects, and timetable slots
into timetable.db
"""

import sqlite3
import datetime

DB_PATH = "timetable.db"

def run_seed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    now = datetime.datetime.now().isoformat()
    # Werkzeug scrypt hash for 'teacher123'
    tch_pass = "scrypt:32768:8:1$TQP559lAkKiSaD8c$5ddcdcae1c450eeffc397d23140a8a8923b61ae46d9ff01d00f496f703591abc4274476f39466f2e8303a62fb8ce28c7e62ff4917ddea2fbdc74ceaed540726a"
    dept_id = "dept_1" # Computer Science & Engineering

    # 1. Update or ensure CSE department exists
    cur.execute("SELECT id FROM departments WHERE id = ?", (dept_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO departments (id, name, code) VALUES (?, ?, ?)",
                    (dept_id, "Computer Science and Engineering", "CSE"))

    # 2. 33 Faculty Members
    faculty_list = [
        ("tch_sjbit_01", "krishna", "Dr. Krishna A N", "krishna.an@sjbit.edu.in", "9876540001", "5th A,B,C&D"),
        ("tch_sjbit_02", "naveena", "Dr. Naveena C", "naveena.c@sjbit.edu.in", "9876540002", "7th A & C, I M. Tech"),
        ("tch_sjbit_03", "bindiya", "Dr. Bindiya M K", "bindiya.mk@sjbit.edu.in", "9876540003", "5th A, I M. Tech"),
        ("tch_sjbit_04", "ajay", "Dr. Ajay B N", "ajay.bn@sjbit.edu.in", "9876540004", "5th D, I M.Tech"),
        ("tch_sjbit_05", "prasad", "Dr. Prasad A Y", "prasad.ay@sjbit.edu.in", "9876540005", "3rd A & B"),
        ("tch_sjbit_06", "shanthakumar", "Dr. Shanthakumar H C", "shanthakumar.hc@sjbit.edu.in", "9876540006", "1st A & B"),
        ("tch_sjbit_07", "veena", "Dr. Veena H N", "veena.hn@sjbit.edu.in", "9876540007", "7th A, I M. Tech"),
        ("tch_sjbit_08", "roopa", "Dr. Roopa M J", "roopa.mj@sjbit.edu.in", "9876540008", "5th C, I M.Tech"),
        ("tch_sjbit_09", "prakruthi_mk", "Dr. Prakruthi M K", "prakruthi.mk@sjbit.edu.in", "9876540009", "5th C & 7th B"),
        ("tch_sjbit_10", "arunkumar", "Dr. Arun Kumar D R", "arunkumar.dr@sjbit.edu.in", "9876540010", "3rd A & B, 5th A, 7th OE"),
        ("tch_sjbit_11", "dhananjaya", "Mr. Dhananjaya M", "dhananjaya.m@sjbit.edu.in", "9876540011", "3rd C & 5th C"),
        ("tch_sjbit_12", "shubha", "Mrs. Shubha T V", "shubha.tv@sjbit.edu.in", "9876540012", "3rd A & 5th B"),
        ("tch_sjbit_13", "lochan", "Mr. Lochan Gowda M", "lochan.gm@sjbit.edu.in", "9876540013", "5th B, I M. Tech"),
        ("tch_sjbit_14", "srinidhi", "Mrs. Srinidhi K S", "srinidhi.ks@sjbit.edu.in", "9876540014", "3rd C, 5th A,B,C&D"),
        ("tch_sjbit_15", "anusha", "Mrs. Anusha M", "anusha.m@sjbit.edu.in", "9876540015", "3rd C & D"),
        ("tch_sjbit_16", "rajeshwari", "Mrs. Rajeshwari G L", "rajeshwari.gl@sjbit.edu.in", "9876540016", "3rd C & D"),
        ("tch_sjbit_17", "jyothi", "Mrs. Jyothi P K", "jyothi.pk@sjbit.edu.in", "9876540017", "3rd A, B, C&D, 5th B, 7th B"),
        ("tch_sjbit_18", "vijayalakshmi", "Mrs. Vijayalakshmi B", "vijayalakshmi.b@sjbit.edu.in", "9876540018", "3rd A, B, C & D, 5th A, B & 7th C, I M. Tech"),
        ("tch_sjbit_19", "rajani", "Mrs. Rajani", "rajani@sjbit.edu.in", "9876540019", "5th A, B, & D"),
        ("tch_sjbit_20", "chetana", "Mrs. Chetana K N", "chetana.kn@sjbit.edu.in", "9876540020", "5th A, B, C, & D, 7th A & B"),
        ("tch_sjbit_21", "shilpashree", "Mrs. Shilpashree S", "shilpashree.s@sjbit.edu.in", "9876540021", "3rd B, 7th B"),
        ("tch_sjbit_22", "vinutha", "Mrs. Vinutha K", "vinutha.k@sjbit.edu.in", "9876540022", "5th A, B, C, & D"),
        ("tch_sjbit_23", "vijayalaxmi_j", "Mrs. Vijayalaxmi Joshi", "vijayalaxmi.j@sjbit.edu.in", "9876540023", "3rd, 5th D & 7th A"),
        ("tch_sjbit_24", "santhosh", "Mr. Santhosh K", "santhosh.k@sjbit.edu.in", "9876540024", "3rd A & 7th C"),
        ("tch_sjbit_25", "shreenagamanjula", "Mrs. Shreenagamanjula Rani", "shreenagamanjula@sjbit.edu.in", "9876540025", "1st C & 3rd B"),
        ("tch_sjbit_26", "bhanumathi", "Mrs. Bhanumathi H R", "bhanumathi.hr@sjbit.edu.in", "9876540026", "3rd B & D"),
        ("tch_sjbit_27", "archana", "Ms. Archana V", "archana.v@sjbit.edu.in", "9876540027", "1st D"),
        ("tch_sjbit_28", "ganga", "Mrs. Ganga B M", "ganga.bm@sjbit.edu.in", "9876540028", "5th D & 7th C"),
        ("tch_sjbit_29", "madhushree", "Mrs. Madhushree V", "madhushree.v@sjbit.edu.in", "9876540029", "1st C & E"),
        ("tch_sjbit_30", "meghana", "Mrs. Meghana N R", "meghana.nr@sjbit.edu.in", "9876540030", "1st B & 5th A"),
        ("tch_sjbit_31", "manjula", "Mrs. Manjula H S", "manjula.hs@sjbit.edu.in", "9876540031", "3rd C & D, 5th B"),
        ("tch_sjbit_32", "suma", "Mrs. Suma B N", "suma.bn@sjbit.edu.in", "9876540032", "3rd A & 5th B, C & D"),
        ("tch_sjbit_33", "prakruthi_gr", "Mrs. Prakruthi G R", "prakruthi.gr@sjbit.edu.in", "9876540033", "5th A, B, C & D")
    ]

    for fid, user, name, email, phone, ugs in faculty_list:
        cur.execute("SELECT id FROM users WHERE username = ?", (user,))
        existing = cur.fetchone()
        if existing:
            cur.execute("""
                UPDATE users SET name = ?, email = ?, phone = ?, department_id = ?
                WHERE username = ?
            """, (name, email, phone, dept_id, user))
        else:
            cur.execute("""
                INSERT INTO users (id, username, password_hash, role, name, email, phone, department_id, created_at)
                VALUES (?, ?, ?, 'teacher', ?, ?, ?, ?, ?)
            """, (fid, user, tch_pass, name, email, phone, dept_id, now))

    # 3. Classrooms
    rooms = [
        ("cls_101", "Room 101 (LH-1)", "classroom", 60, "CSE Academic Block"),
        ("cls_102", "Room 102 (LH-2)", "classroom", 60, "CSE Academic Block"),
        ("cls_103", "Room 103 (LH-3)", "classroom", 60, "CSE Academic Block"),
        ("cls_104", "Room 104 (LH-4)", "classroom", 60, "CSE Academic Block"),
        ("cls_lab1", "Computer Lab 1 (CC-1)", "lab", 40, "SJBIT Tech Wing"),
        ("cls_lab2", "Computer Lab 2 (CC-2)", "lab", 40, "SJBIT Tech Wing"),
        ("cls_lab3", "Data Science & AI Lab", "lab", 40, "SJBIT Tech Wing"),
        ("cls_lab4", "Networks & Cloud Lab", "lab", 40, "SJBIT Tech Wing"),
        ("cls_lab5", "Hardware & Logic Design Lab", "lab", 40, "Electronics Block")
    ]
    for rid, rname, rtype, rcap, rbld in rooms:
        cur.execute("INSERT OR REPLACE INTO classrooms (id, name, type, capacity, building) VALUES (?, ?, ?, ?, ?)",
                    (rid, rname, rtype, rcap, rbld))

    # 4. Cohorts & Timetables
    cohorts = [
        # Sem 1
        (1, 1, "A"), (1, 1, "B"), (1, 1, "C"), (1, 1, "D"), (1, 1, "E"),
        # Sem 3
        (2, 3, "A"), (2, 3, "B"), (2, 3, "C"), (2, 3, "D"),
        # Sem 5
        (3, 5, "A"), (3, 5, "B"), (3, 5, "C"), (3, 5, "D"),
        # Sem 7
        (4, 7, "A"), (4, 7, "B"), (4, 7, "C"),
        # M.Tech
        (1, 1, "MTech")
    ]

    for yr, sem, sec in cohorts:
        tt_id = f"tt_{dept_id}_{yr}_{sem}_{sec}"
        cur.execute("INSERT OR IGNORE INTO timetables (id, department_id, year, semester, section, published, generated_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
                    (tt_id, dept_id, yr, sem, sec, now, now))

    # 5. Helper to insert subject and slot
    # Dictionary of subjects: code -> (id, name, type, year, semester)
    subject_catalog = {}

    def get_or_create_sub(code, name, stype, yr, sem, teacher_id):
        key = f"{code}_{sem}_{stype}"
        if key in subject_catalog:
            return subject_catalog[key]
        sub_id = f"sub_{code.lower().replace('&', '_').replace(' ', '_').replace('(', '').replace(')', '')}_{sem}_{yr}"
        cur.execute("""
            INSERT OR REPLACE INTO subjects (id, name, code, department_id, year, semester, type, hours_per_week, teacher_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 4, ?)
        """, (sub_id, name, code, dept_id, yr, sem, stype, teacher_id))
        subject_catalog[key] = sub_id
        return sub_id

    # Raw Schedule Data from the SJBIT Document for each teacher:
    # (teacher_user, day, period, subject_code, subject_name, slot_type, year, sem, section, room_id)
    # Period times:
    # 1: 08:30-09:30, 2: 09:30-10:30, 3: 10:45-11:45, 4: 11:45-12:45, 5: 01:30-02:30, 6: 02:30-03:30, 7: 03:30-04:30
    schedule_data = [
        # 1. Dr. Krishna A N (5th A,B,C&D)
        ("krishna", "Monday", 5, "DIP", "Digital Image Processing", "theory", 3, 5, "A", "cls_101"),
        ("krishna", "Thursday", 3, "DIP", "Digital Image Processing", "theory", 3, 5, "B", "cls_102"),
        ("krishna", "Friday", 5, "DIP", "Digital Image Processing", "theory", 3, 5, "C", "cls_103"),

        # 2. Dr. Naveena C (7th A & C, I M.Tech)
        ("naveena", "Monday", 1, "HPC(A)", "High Performance Computing", "theory", 4, 7, "A", "cls_101"),
        ("naveena", "Monday", 5, "HPC(C)", "High Performance Computing", "theory", 4, 7, "C", "cls_102"),
        ("naveena", "Tuesday", 1, "NLP", "Natural Language Processing", "theory", 4, 7, "A", "cls_101"),
        ("naveena", "Tuesday", 2, "HPC(C)", "High Performance Computing", "theory", 4, 7, "C", "cls_102"),
        ("naveena", "Tuesday", 3, "NLP", "Natural Language Processing", "theory", 4, 7, "C", "cls_102"),
        ("naveena", "Tuesday", 5, "HPC(A)", "High Performance Computing", "theory", 4, 7, "A", "cls_101"),
        ("naveena", "Wednesday", 1, "HPC(C)", "High Performance Computing", "theory", 4, 7, "C", "cls_102"),
        ("naveena", "Wednesday", 4, "HPC(A)", "High Performance Computing", "theory", 4, 7, "A", "cls_101"),
        ("naveena", "Thursday", 2, "NLP", "Natural Language Processing", "theory", 4, 7, "A", "cls_101"),
        ("naveena", "Friday", 4, "NLP", "Natural Language Processing", "theory", 4, 7, "C", "cls_102"),

        # 3. Dr. Bindiya M K (5th A, I M.Tech)
        ("bindiya", "Monday", 2, "NoSql", "NoSQL Databases", "theory", 3, 5, "A", "cls_101"),
        ("bindiya", "Monday", 4, "DBMS", "Database Management Systems", "theory", 3, 5, "A", "cls_101"),
        ("bindiya", "Monday", 7, "NoSql", "NoSQL Databases", "theory", 3, 5, "A", "cls_101"),
        ("bindiya", "Tuesday", 1, "DBMS Lab(A2)", "DBMS Laboratory", "lab", 3, 5, "A", "cls_lab1"),
        ("bindiya", "Tuesday", 2, "DBMS Lab(A2)", "DBMS Laboratory", "lab", 3, 5, "A", "cls_lab1"),
        ("bindiya", "Tuesday", 3, "DBMS", "Database Management Systems", "theory", 3, 5, "A", "cls_101"),
        ("bindiya", "Thursday", 1, "DBMS Lab(A3)", "DBMS Laboratory", "lab", 3, 5, "A", "cls_lab1"),
        ("bindiya", "Thursday", 2, "DBMS Lab(A3)", "DBMS Laboratory", "lab", 3, 5, "A", "cls_lab1"),
        ("bindiya", "Thursday", 5, "DBMS", "Database Management Systems", "theory", 3, 5, "A", "cls_101"),
        ("bindiya", "Friday", 1, "NoSql", "NoSQL Databases", "theory", 3, 5, "A", "cls_101"),
        ("bindiya", "Friday", 3, "DBMS Lab(A1)", "DBMS Laboratory", "lab", 3, 5, "A", "cls_lab1"),
        ("bindiya", "Friday", 4, "DBMS Lab(A1)", "DBMS Laboratory", "lab", 3, 5, "A", "cls_lab1"),

        # 4. Dr. Ajay B N (5th D, I M.Tech)
        ("ajay", "Monday", 2, "DBMS", "Database Management Systems", "theory", 3, 5, "D", "cls_104"),
        ("ajay", "Monday", 6, "RM&IPR", "Research Methodology & IPR", "theory", 3, 5, "D", "cls_104"),
        ("ajay", "Tuesday", 2, "RM&IPR", "Research Methodology & IPR", "theory", 3, 5, "D", "cls_104"),
        ("ajay", "Tuesday", 3, "DBMS Lab(D2)", "DBMS Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("ajay", "Tuesday", 4, "DBMS Lab(D2)", "DBMS Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("ajay", "Tuesday", 6, "DBMS", "Database Management Systems", "theory", 3, 5, "D", "cls_104"),
        ("ajay", "Wednesday", 1, "DBMS Lab(D3)", "DBMS Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("ajay", "Wednesday", 2, "DBMS Lab(D3)", "DBMS Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("ajay", "Thursday", 4, "DBMS", "Database Management Systems", "theory", 3, 5, "D", "cls_104"),
        ("ajay", "Friday", 1, "DBMS Lab(D1)", "DBMS Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("ajay", "Friday", 2, "DBMS Lab(D1)", "DBMS Laboratory", "lab", 3, 5, "D", "cls_lab2"),

        # 5. Dr. Prasad A Y (3rd A & B)
        ("prasad", "Monday", 3, "CO", "Computer Organization", "theory", 2, 3, "A", "cls_101"),
        ("prasad", "Tuesday", 2, "LD", "Logic Design", "theory", 2, 3, "B", "cls_102"),
        ("prasad", "Tuesday", 5, "CO", "Computer Organization", "theory", 2, 3, "A", "cls_101"),
        ("prasad", "Tuesday", 6, "LD Lab(B1)", "Logic Design Lab", "lab", 2, 3, "B", "cls_lab5"),
        ("prasad", "Tuesday", 7, "LD Lab(B1)", "Logic Design Lab", "lab", 2, 3, "B", "cls_lab5"),
        ("prasad", "Wednesday", 1, "LD Lab(B2)", "Logic Design Lab", "lab", 2, 3, "B", "cls_lab5"),
        ("prasad", "Wednesday", 2, "LD Lab(B2)", "Logic Design Lab", "lab", 2, 3, "B", "cls_lab5"),
        ("prasad", "Wednesday", 4, "LD", "Logic Design", "theory", 2, 3, "B", "cls_102"),
        ("prasad", "Thursday", 1, "LD", "Logic Design", "theory", 2, 3, "B", "cls_102"),
        ("prasad", "Friday", 1, "CO", "Computer Organization", "theory", 2, 3, "A", "cls_101"),
        ("prasad", "Friday", 3, "LD Lab(B3)", "Logic Design Lab", "lab", 2, 3, "B", "cls_lab5"),
        ("prasad", "Friday", 4, "LD Lab(B3)", "Logic Design Lab", "lab", 2, 3, "B", "cls_lab5"),

        # 6. Dr. Shanthakumar H C (1st A & B)
        ("shanthakumar", "Monday", 3, "PLT(A)", "Programming Language Tools", "theory", 1, 1, "A", "cls_101"),
        ("shanthakumar", "Monday", 5, "PLT Lab(A3)", "PLT Laboratory", "lab", 1, 1, "A", "cls_lab1"),
        ("shanthakumar", "Monday", 6, "PLT Lab(A3)", "PLT Laboratory", "lab", 1, 1, "A", "cls_lab1"),
        ("shanthakumar", "Tuesday", 4, "PLT(B)", "Programming Language Tools", "theory", 1, 1, "B", "cls_102"),
        ("shanthakumar", "Wednesday", 4, "PLT(B)", "Programming Language Tools", "theory", 1, 1, "B", "cls_102"),
        ("shanthakumar", "Thursday", 1, "PLT Lab(A1)", "PLT Laboratory", "lab", 1, 1, "A", "cls_lab1"),
        ("shanthakumar", "Thursday", 2, "PLT Lab(A1)", "PLT Laboratory", "lab", 1, 1, "A", "cls_lab1"),
        ("shanthakumar", "Thursday", 6, "PLT(A)", "Programming Language Tools", "theory", 1, 1, "A", "cls_101"),
        ("shanthakumar", "Friday", 1, "PLT Lab(A2)", "PLT Laboratory", "lab", 1, 1, "A", "cls_lab1"),
        ("shanthakumar", "Friday", 2, "PLT Lab(A2)", "PLT Laboratory", "lab", 1, 1, "A", "cls_lab1"),
        ("shanthakumar", "Friday", 3, "PLT(A)", "Programming Language Tools", "theory", 1, 1, "A", "cls_101"),
        ("shanthakumar", "Friday", 5, "PLT(B)", "Programming Language Tools", "theory", 1, 1, "B", "cls_102"),

        # 7. Dr. Veena H N (7th A, I M.Tech)
        ("veena", "Monday", 2, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "A", "cls_101"),
        ("veena", "Monday", 4, "IP&CV", "Image Processing & Computer Vision", "theory", 4, 7, "A", "cls_101"),
        ("veena", "Monday", 6, "GAI&PE Lab(A1)", "GAI&PE Laboratory", "lab", 4, 7, "A", "cls_lab3"),
        ("veena", "Monday", 7, "GAI&PE Lab(A1)", "GAI&PE Laboratory", "lab", 4, 7, "A", "cls_lab3"),
        ("veena", "Tuesday", 1, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "A", "cls_101"),
        ("veena", "Tuesday", 3, "IP&CV", "Image Processing & Computer Vision", "theory", 4, 7, "A", "cls_101"),
        ("veena", "Tuesday", 6, "GAI&PE Lab(A2)", "GAI&PE Laboratory", "lab", 4, 7, "A", "cls_lab3"),
        ("veena", "Tuesday", 7, "GAI&PE Lab(A2)", "GAI&PE Laboratory", "lab", 4, 7, "A", "cls_lab3"),
        ("veena", "Wednesday", 2, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "A", "cls_101"),
        ("veena", "Wednesday", 5, "GAI&PE Lab(A3)", "GAI&PE Laboratory", "lab", 4, 7, "A", "cls_lab3"),
        ("veena", "Wednesday", 6, "GAI&PE Lab(A3)", "GAI&PE Laboratory", "lab", 4, 7, "A", "cls_lab3"),
        ("veena", "Friday", 3, "IP&CV", "Image Processing & Computer Vision", "theory", 4, 7, "A", "cls_101"),

        # 8. Dr. Roopa M J (5th C, I M.Tech)
        ("roopa", "Monday", 4, "DBMS", "Database Management Systems", "theory", 3, 5, "C", "cls_103"),
        ("roopa", "Monday", 5, "LA", "Linear Algebra", "theory", 3, 5, "C", "cls_103"),
        ("roopa", "Tuesday", 1, "DBMS Lab(C2)", "DBMS Laboratory", "lab", 3, 5, "C", "cls_lab1"),
        ("roopa", "Tuesday", 2, "DBMS Lab(C2)", "DBMS Laboratory", "lab", 3, 5, "C", "cls_lab1"),
        ("roopa", "Tuesday", 3, "LA", "Linear Algebra", "theory", 3, 5, "C", "cls_103"),
        ("roopa", "Wednesday", 1, "DBMS", "Database Management Systems", "theory", 3, 5, "C", "cls_103"),
        ("roopa", "Wednesday", 3, "LA", "Linear Algebra", "theory", 3, 5, "C", "cls_103"),
        ("roopa", "Thursday", 1, "DBMS Lab(C3)", "DBMS Laboratory", "lab", 3, 5, "C", "cls_lab1"),
        ("roopa", "Thursday", 2, "DBMS Lab(C3)", "DBMS Laboratory", "lab", 3, 5, "C", "cls_lab1"),
        ("roopa", "Thursday", 3, "DBMS", "Database Management Systems", "theory", 3, 5, "C", "cls_103"),
        ("roopa", "Friday", 2, "LA", "Linear Algebra", "theory", 3, 5, "C", "cls_103"),
        ("roopa", "Friday", 3, "DBMS Lab(C1)", "DBMS Laboratory", "lab", 3, 5, "C", "cls_lab1"),
        ("roopa", "Friday", 4, "DBMS Lab(C1)", "DBMS Laboratory", "lab", 3, 5, "C", "cls_lab1"),

        # 9. Dr. Prakruthi M K (5th C & 7th B)
        ("prakruthi_mk", "Monday", 1, "HPC", "High Performance Computing", "theory", 4, 7, "B", "cls_102"),
        ("prakruthi_mk", "Monday", 6, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "C", "cls_103"),
        ("prakruthi_mk", "Tuesday", 1, "SE&PM Lab(C1)", "SE&PM Laboratory", "lab", 3, 5, "C", "cls_lab2"),
        ("prakruthi_mk", "Tuesday", 2, "SE&PM Lab(C1)", "SE&PM Laboratory", "lab", 3, 5, "C", "cls_lab2"),
        ("prakruthi_mk", "Tuesday", 7, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "C", "cls_103"),
        ("prakruthi_mk", "Wednesday", 2, "HPC", "High Performance Computing", "theory", 4, 7, "B", "cls_102"),
        ("prakruthi_mk", "Wednesday", 4, "HPC", "High Performance Computing", "theory", 4, 7, "B", "cls_102"),
        ("prakruthi_mk", "Thursday", 1, "SE&PM Lab(C2)", "SE&PM Laboratory", "lab", 3, 5, "C", "cls_lab2"),
        ("prakruthi_mk", "Thursday", 2, "SE&PM Lab(C2)", "SE&PM Laboratory", "lab", 3, 5, "C", "cls_lab2"),
        ("prakruthi_mk", "Friday", 1, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "C", "cls_103"),
        ("prakruthi_mk", "Friday", 3, "SE&PM Lab(C3)", "SE&PM Laboratory", "lab", 3, 5, "C", "cls_lab2"),
        ("prakruthi_mk", "Friday", 4, "SE&PM Lab(C3)", "SE&PM Laboratory", "lab", 3, 5, "C", "cls_lab2"),

        # 10. Dr. Arun Kumar D R (3rd A & B, 5th A, 7th OE)
        ("arunkumar", "Monday", 4, "OE", "Open Elective", "theory", 4, 7, "A", "cls_101"),
        ("arunkumar", "Monday", 6, "LCS Lab(B1)", "Linux & Cloud Lab", "lab", 2, 3, "B", "cls_lab4"),
        ("arunkumar", "Monday", 7, "LCS Lab(B1)", "Linux & Cloud Lab", "lab", 2, 3, "B", "cls_lab4"),
        ("arunkumar", "Tuesday", 4, "OE", "Open Elective", "theory", 4, 7, "B", "cls_102"),
        ("arunkumar", "Tuesday", 6, "A.JAVA", "Advanced Java", "theory", 3, 5, "A", "cls_101"),
        ("arunkumar", "Wednesday", 2, "A.JAVA", "Advanced Java", "theory", 3, 5, "A", "cls_101"),
        ("arunkumar", "Wednesday", 3, "OE", "Open Elective", "theory", 4, 7, "C", "cls_103"),
        ("arunkumar", "Wednesday", 6, "LCS Lab(B2)", "Linux & Cloud Lab", "lab", 2, 3, "B", "cls_lab4"),
        ("arunkumar", "Wednesday", 7, "LCS Lab(B2)", "Linux & Cloud Lab", "lab", 2, 3, "B", "cls_lab4"),
        ("arunkumar", "Friday", 1, "A.JAVA", "Advanced Java", "theory", 3, 5, "A", "cls_101"),

        # 11. Mr. Dhananjaya M (3rd C & 5th C)
        ("dhananjaya", "Monday", 2, "A.JAVA", "Advanced Java", "theory", 3, 5, "C", "cls_103"),
        ("dhananjaya", "Monday", 3, "DSA Lab(C2)", "Data Structures Lab", "lab", 2, 3, "C", "cls_lab3"),
        ("dhananjaya", "Monday", 4, "DSA Lab(C2)", "Data Structures Lab", "lab", 2, 3, "C", "cls_lab3"),
        ("dhananjaya", "Monday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "C", "cls_103"),
        ("dhananjaya", "Tuesday", 2, "DSA", "Data Structures", "theory", 2, 3, "C", "cls_103"),
        ("dhananjaya", "Tuesday", 3, "DSA Lab(C3)", "Data Structures Lab", "lab", 2, 3, "C", "cls_lab3"),
        ("dhananjaya", "Tuesday", 4, "DSA Lab(C3)", "Data Structures Lab", "lab", 2, 3, "C", "cls_lab3"),
        ("dhananjaya", "Wednesday", 2, "A.JAVA", "Advanced Java", "theory", 3, 5, "C", "cls_103"),
        ("dhananjaya", "Wednesday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "C", "cls_103"),
        ("dhananjaya", "Thursday", 1, "DSA Lab(C1)", "Data Structures Lab", "lab", 2, 3, "C", "cls_lab3"),
        ("dhananjaya", "Thursday", 2, "DSA Lab(C1)", "Data Structures Lab", "lab", 2, 3, "C", "cls_lab3"),
        ("dhananjaya", "Thursday", 3, "DSA", "Data Structures", "theory", 2, 3, "C", "cls_103"),
        ("dhananjaya", "Thursday", 5, "A.JAVA", "Advanced Java", "theory", 3, 5, "C", "cls_103"),
        ("dhananjaya", "Friday", 1, "DSA", "Data Structures", "theory", 2, 3, "C", "cls_103"),

        # 12. Mrs. Shubha T V (3rd A & 5th B)
        ("shubha", "Monday", 2, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "B", "cls_102"),
        ("shubha", "Monday", 5, "DSA", "Data Structures", "theory", 2, 3, "A", "cls_101"),
        ("shubha", "Tuesday", 1, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "B", "cls_102"),
        ("shubha", "Tuesday", 3, "DSA", "Data Structures", "theory", 2, 3, "A", "cls_101"),
        ("shubha", "Tuesday", 6, "DSA Lab(A2)", "Data Structures Lab", "lab", 2, 3, "A", "cls_lab1"),
        ("shubha", "Tuesday", 7, "DSA Lab(A2)", "Data Structures Lab", "lab", 2, 3, "A", "cls_lab1"),
        ("shubha", "Wednesday", 1, "DSA Lab(A3)", "Data Structures Lab", "lab", 2, 3, "A", "cls_lab1"),
        ("shubha", "Wednesday", 2, "DSA Lab(A3)", "Data Structures Lab", "lab", 2, 3, "A", "cls_lab1"),
        ("shubha", "Wednesday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "A", "cls_101"),
        ("shubha", "Thursday", 2, "DSA", "Data Structures", "theory", 2, 3, "A", "cls_101"),
        ("shubha", "Thursday", 4, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "B", "cls_102"),
        ("shubha", "Friday", 3, "DSA Lab(A1)", "Data Structures Lab", "lab", 2, 3, "A", "cls_lab1"),
        ("shubha", "Friday", 4, "DSA Lab(A1)", "Data Structures Lab", "lab", 2, 3, "A", "cls_lab1"),
        ("shubha", "Friday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "A", "cls_101"),

        # 13. Mr. Lochan Gowda M (5th B, I M.Tech)
        ("lochan", "Monday", 1, "CNS", "Cryptography & Network Security", "theory", 3, 5, "B", "cls_102"),
        ("lochan", "Monday", 3, "CNS", "Cryptography & Network Security", "theory", 3, 5, "B", "cls_102"),
        ("lochan", "Monday", 6, "CN", "Computer Networks", "theory", 3, 5, "B", "cls_102"),
        ("lochan", "Tuesday", 2, "CN", "Computer Networks", "theory", 3, 5, "B", "cls_102"),
        ("lochan", "Tuesday", 3, "CN Lab(B3)", "Computer Networks Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Tuesday", 4, "CN Lab(B3)", "Computer Networks Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Wednesday", 1, "CN Lab(B1)", "Computer Networks Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Wednesday", 2, "CN Lab(B1)", "Computer Networks Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Wednesday", 3, "CNS", "Cryptography & Network Security", "theory", 3, 5, "B", "cls_102"),
        ("lochan", "Thursday", 1, "CNS", "Cryptography & Network Security", "theory", 3, 5, "B", "cls_102"),
        ("lochan", "Thursday", 3, "CNS Lab", "CNS Laboratory", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Thursday", 4, "CNS Lab", "CNS Laboratory", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Friday", 1, "CN Lab(B2)", "Computer Networks Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Friday", 2, "CN Lab(B2)", "Computer Networks Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("lochan", "Friday", 3, "CN", "Computer Networks", "theory", 3, 5, "B", "cls_102"),

        # 14. Mrs. Srinidhi K S (3rd C, 5th A,B,C&D)
        ("srinidhi", "Monday", 2, "OS", "Operating Systems", "theory", 2, 3, "C", "cls_103"),
        ("srinidhi", "Monday", 5, "React JS", "React JS Development", "theory", 3, 5, "A", "cls_101"),
        ("srinidhi", "Wednesday", 2, "OS", "Operating Systems", "theory", 2, 3, "C", "cls_103"),
        ("srinidhi", "Wednesday", 3, "CC Lab(B7)", "Cloud Computing Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("srinidhi", "Wednesday", 4, "CC Lab(B7)", "Cloud Computing Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("srinidhi", "Thursday", 3, "React JS", "React JS Development", "theory", 3, 5, "B", "cls_102"),
        ("srinidhi", "Thursday", 6, "CC Lab(B8)", "Cloud Computing Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("srinidhi", "Thursday", 7, "CC Lab(B8)", "Cloud Computing Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("srinidhi", "Friday", 2, "OS", "Operating Systems", "theory", 2, 3, "C", "cls_103"),
        ("srinidhi", "Friday", 5, "React JS", "React JS Development", "theory", 3, 5, "C", "cls_103"),
        ("srinidhi", "Friday", 6, "CC Lab(B9)", "Cloud Computing Lab", "lab", 3, 5, "D", "cls_lab4"),
        ("srinidhi", "Friday", 7, "CC Lab(B9)", "Cloud Computing Lab", "lab", 3, 5, "D", "cls_lab4"),

        # 15. Mrs. Anusha M (3rd C & D)
        ("anusha", "Monday", 3, "DSA Lab(D2)", "Data Structures Lab", "lab", 2, 3, "D", "cls_lab3"),
        ("anusha", "Monday", 4, "DSA Lab(D2)", "Data Structures Lab", "lab", 2, 3, "D", "cls_lab3"),
        ("anusha", "Monday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "D", "cls_104"),
        ("anusha", "Tuesday", 1, "DSA", "Data Structures", "theory", 2, 3, "D", "cls_104"),
        ("anusha", "Tuesday", 3, "DSA Lab(D3)", "Data Structures Lab", "lab", 2, 3, "D", "cls_lab3"),
        ("anusha", "Tuesday", 4, "DSA Lab(D3)", "Data Structures Lab", "lab", 2, 3, "D", "cls_lab3"),
        ("anusha", "Tuesday", 7, "CO", "Computer Organization", "theory", 2, 3, "D", "cls_104"),
        ("anusha", "Wednesday", 3, "CO", "Computer Organization", "theory", 2, 3, "D", "cls_104"),
        ("anusha", "Wednesday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "D", "cls_104"),
        ("anusha", "Thursday", 1, "DSA Lab(D1)", "Data Structures Lab", "lab", 2, 3, "D", "cls_lab3"),
        ("anusha", "Thursday", 2, "DSA Lab(D1)", "Data Structures Lab", "lab", 2, 3, "D", "cls_lab3"),
        ("anusha", "Thursday", 3, "DSA", "Data Structures", "theory", 2, 3, "D", "cls_104"),
        ("anusha", "Friday", 2, "DSA", "Data Structures", "theory", 2, 3, "D", "cls_104"),
        ("anusha", "Friday", 4, "CO", "Computer Organization", "theory", 2, 3, "D", "cls_104"),

        # 16. Mrs. Rajeshwari G L (3rd C & D)
        ("rajeshwari", "Monday", 3, "LD Lab(C1)", "Logic Design Lab", "lab", 2, 3, "C", "cls_lab5"),
        ("rajeshwari", "Monday", 4, "LD Lab(C1)", "Logic Design Lab", "lab", 2, 3, "C", "cls_lab5"),
        ("rajeshwari", "Tuesday", 1, "LD", "Logic Design", "theory", 2, 3, "C", "cls_103"),
        ("rajeshwari", "Tuesday", 3, "LD Lab(C2)", "Logic Design Lab", "lab", 2, 3, "C", "cls_lab5"),
        ("rajeshwari", "Tuesday", 4, "LD Lab(C2)", "Logic Design Lab", "lab", 2, 3, "C", "cls_lab5"),
        ("rajeshwari", "Tuesday", 5, "CO", "Computer Organization", "theory", 2, 3, "C", "cls_103"),
        ("rajeshwari", "Wednesday", 2, "CO", "Computer Organization", "theory", 2, 3, "C", "cls_103"),
        ("rajeshwari", "Wednesday", 4, "LD", "Logic Design", "theory", 2, 3, "C", "cls_103"),
        ("rajeshwari", "Thursday", 1, "LD Lab(C3)", "Logic Design Lab", "lab", 2, 3, "C", "cls_lab5"),
        ("rajeshwari", "Thursday", 2, "LD Lab(C3)", "Logic Design Lab", "lab", 2, 3, "C", "cls_lab5"),
        ("rajeshwari", "Friday", 1, "CO", "Computer Organization", "theory", 2, 3, "C", "cls_103"),
        ("rajeshwari", "Friday", 3, "LD", "Logic Design", "theory", 2, 3, "C", "cls_103"),

        # 17. Mrs. Jyothi P K (3rd A,B,C&D, 5th B, 7th B)
        ("jyothi", "Monday", 3, "ME", "Management & Entrepreneurship", "theory", 2, 3, "A", "cls_101"),
        ("jyothi", "Monday", 6, "LCS Lab(B3)", "Linux & Cloud Lab", "lab", 2, 3, "B", "cls_lab4"),
        ("jyothi", "Monday", 7, "LCS Lab(B3)", "Linux & Cloud Lab", "lab", 2, 3, "B", "cls_lab4"),
        ("jyothi", "Tuesday", 2, "ME", "Management & Entrepreneurship", "theory", 2, 3, "B", "cls_102"),
        ("jyothi", "Tuesday", 3, "DBMS Lab(B2)", "DBMS Laboratory", "lab", 3, 5, "B", "cls_lab1"),
        ("jyothi", "Tuesday", 4, "DBMS Lab(B2)", "DBMS Laboratory", "lab", 3, 5, "B", "cls_lab1"),
        ("jyothi", "Tuesday", 5, "DBMS", "Database Management Systems", "theory", 3, 5, "B", "cls_102"),
        ("jyothi", "Wednesday", 1, "DBMS Lab(B3)", "DBMS Laboratory", "lab", 3, 5, "B", "cls_lab1"),
        ("jyothi", "Wednesday", 2, "DBMS Lab(B3)", "DBMS Laboratory", "lab", 3, 5, "B", "cls_lab1"),
        ("jyothi", "Thursday", 5, "DBMS", "Database Management Systems", "theory", 3, 5, "B", "cls_102"),
        ("jyothi", "Friday", 1, "DBMS Lab(B1)", "DBMS Laboratory", "lab", 3, 5, "B", "cls_lab1"),
        ("jyothi", "Friday", 2, "DBMS Lab(B1)", "DBMS Laboratory", "lab", 3, 5, "B", "cls_lab1"),
        ("jyothi", "Friday", 3, "DBMS", "Database Management Systems", "theory", 3, 5, "B", "cls_102"),

        # 18. Mrs. Vijayalakshmi B (3rd A,B,C&D, 5th A,B & 7th C, I M.Tech)
        ("vijayalakshmi", "Monday", 3, "ME", "Management & Entrepreneurship", "theory", 2, 3, "C", "cls_103"),
        ("vijayalakshmi", "Monday", 5, "React JS", "React JS Development", "theory", 3, 5, "B", "cls_102"),
        ("vijayalakshmi", "Monday", 6, "Web Lab(B1)", "Web Development Lab", "lab", 3, 5, "B", "cls_lab3"),
        ("vijayalakshmi", "Monday", 7, "Web Lab(B1)", "Web Development Lab", "lab", 3, 5, "B", "cls_lab3"),
        ("vijayalakshmi", "Tuesday", 3, "ME", "Management & Entrepreneurship", "theory", 2, 3, "D", "cls_104"),
        ("vijayalakshmi", "Wednesday", 1, "NoSql Lab", "NoSQL Laboratory", "lab", 3, 5, "A", "cls_lab3"),
        ("vijayalakshmi", "Wednesday", 2, "NoSql Lab", "NoSQL Laboratory", "lab", 3, 5, "A", "cls_lab3"),
        ("vijayalakshmi", "Wednesday", 6, "Web Lab(B2)", "Web Development Lab", "lab", 3, 5, "B", "cls_lab3"),
        ("vijayalakshmi", "Wednesday", 7, "Web Lab(B2)", "Web Development Lab", "lab", 3, 5, "B", "cls_lab3"),
        ("vijayalakshmi", "Thursday", 3, "React JS", "React JS Development", "theory", 3, 5, "A", "cls_101"),
        ("vijayalakshmi", "Friday", 5, "React JS", "React JS Development", "theory", 3, 5, "B", "cls_102"),

        # 19. Mrs. Rajani (5th A, B, & D)
        ("rajani", "Monday", 1, "A.JAVA(B)", "Advanced Java", "theory", 3, 5, "B", "cls_102"),
        ("rajani", "Monday", 3, "A.JAVA(D)", "Advanced Java", "theory", 3, 5, "D", "cls_104"),
        ("rajani", "Tuesday", 1, "A.JAVA(D)", "Advanced Java", "theory", 3, 5, "D", "cls_104"),
        ("rajani", "Tuesday", 7, "A.JAVA(B)", "Advanced Java", "theory", 3, 5, "B", "cls_102"),
        ("rajani", "Wednesday", 3, "CC Lab(B1)", "Cloud Computing Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("rajani", "Wednesday", 4, "CC Lab(B1)", "Cloud Computing Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("rajani", "Thursday", 2, "A.JAVA(B)", "Advanced Java", "theory", 3, 5, "B", "cls_102"),
        ("rajani", "Thursday", 6, "CC Lab(B2)", "Cloud Computing Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("rajani", "Thursday", 7, "CC Lab(B2)", "Cloud Computing Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("rajani", "Friday", 3, "A.JAVA(D)", "Advanced Java", "theory", 3, 5, "D", "cls_104"),
        ("rajani", "Friday", 6, "CC Lab(B3)", "Cloud Computing Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("rajani", "Friday", 7, "CC Lab(B3)", "Cloud Computing Lab", "lab", 3, 5, "A", "cls_lab4"),

        # 20. Mrs. Chetana K N (5th A, B, C, & D, 7th A & B)
        ("chetana", "Monday", 2, "LC/NC(B)", "Linear Control / Networks", "theory", 3, 5, "B", "cls_102"),
        ("chetana", "Monday", 5, "LC/NC(A)", "Linear Control / Networks", "theory", 3, 5, "A", "cls_101"),
        ("chetana", "Tuesday", 1, "LC/NC(B)", "Linear Control / Networks", "theory", 3, 5, "B", "cls_102"),
        ("chetana", "Tuesday", 3, "LC/NC(A)", "Linear Control / Networks", "theory", 3, 5, "A", "cls_101"),
        ("chetana", "Tuesday", 5, "LC/NC(B)", "Linear Control / Networks", "theory", 3, 5, "B", "cls_102"),
        ("chetana", "Wednesday", 1, "LC/NC(A)", "Linear Control / Networks", "theory", 3, 5, "A", "cls_101"),
        ("chetana", "Wednesday", 3, "Devops(B1)", "DevOps Laboratory", "lab", 4, 7, "A", "cls_lab4"),
        ("chetana", "Wednesday", 4, "Devops(B1)", "DevOps Laboratory", "lab", 4, 7, "A", "cls_lab4"),
        ("chetana", "Thursday", 6, "Devops(B2)", "DevOps Laboratory", "lab", 4, 7, "B", "cls_lab4"),
        ("chetana", "Thursday", 7, "Devops(B2)", "DevOps Laboratory", "lab", 4, 7, "B", "cls_lab4"),
        ("chetana", "Friday", 6, "Devops(B3)", "DevOps Laboratory", "lab", 4, 7, "A", "cls_lab4"),
        ("chetana", "Friday", 7, "Devops(B3)", "DevOps Laboratory", "lab", 4, 7, "A", "cls_lab4"),

        # 21. Mrs. Shilpashree S (3rd B, 7th B)
        ("shilpashree", "Monday", 2, "OS", "Operating Systems", "theory", 2, 3, "B", "cls_102"),
        ("shilpashree", "Monday", 5, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "B", "cls_102"),
        ("shilpashree", "Monday", 6, "GAI&PE Lab(B1)", "GAI&PE Laboratory", "lab", 4, 7, "B", "cls_lab3"),
        ("shilpashree", "Monday", 7, "GAI&PE Lab(B1)", "GAI&PE Laboratory", "lab", 4, 7, "B", "cls_lab3"),
        ("shilpashree", "Tuesday", 1, "OS", "Operating Systems", "theory", 2, 3, "B", "cls_102"),
        ("shilpashree", "Tuesday", 3, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "B", "cls_102"),
        ("shilpashree", "Tuesday", 6, "GAI&PE Lab(B2)", "GAI&PE Laboratory", "lab", 4, 7, "B", "cls_lab3"),
        ("shilpashree", "Tuesday", 7, "GAI&PE Lab(B2)", "GAI&PE Laboratory", "lab", 4, 7, "B", "cls_lab3"),
        ("shilpashree", "Wednesday", 1, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "B", "cls_102"),
        ("shilpashree", "Wednesday", 5, "GAI&PE Lab(B3)", "GAI&PE Laboratory", "lab", 4, 7, "B", "cls_lab3"),
        ("shilpashree", "Wednesday", 6, "GAI&PE Lab(B3)", "GAI&PE Laboratory", "lab", 4, 7, "B", "cls_lab3"),
        ("shilpashree", "Thursday", 3, "OS", "Operating Systems", "theory", 2, 3, "B", "cls_102"),

        # 22. Mrs. Vinutha K (5th A, B, C, & D)
        ("vinutha", "Monday", 1, "CN", "Computer Networks", "theory", 3, 5, "C", "cls_103"),
        ("vinutha", "Monday", 5, "DVT", "Data Visualization Techniques", "theory", 3, 5, "C", "cls_103"),
        ("vinutha", "Tuesday", 1, "CN Lab(C3)", "Computer Networks Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("vinutha", "Tuesday", 2, "CN Lab(C3)", "Computer Networks Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("vinutha", "Tuesday", 3, "CN", "Computer Networks", "theory", 3, 5, "C", "cls_103"),
        ("vinutha", "Thursday", 1, "CN Lab(C1)", "Computer Networks Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("vinutha", "Thursday", 2, "CN Lab(C1)", "Computer Networks Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("vinutha", "Thursday", 3, "DVT", "Data Visualization Techniques", "theory", 3, 5, "C", "cls_103"),
        ("vinutha", "Friday", 2, "CN", "Computer Networks", "theory", 3, 5, "C", "cls_103"),
        ("vinutha", "Friday", 3, "CN Lab(C2)", "Computer Networks Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("vinutha", "Friday", 4, "CN Lab(C2)", "Computer Networks Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("vinutha", "Friday", 5, "DVT", "Data Visualization Techniques", "theory", 3, 5, "C", "cls_103"),

        # 23. Mrs. Vijayalaxmi Joshi (3rd, 5th D & 7th A)
        ("vijayalaxmi_j", "Monday", 1, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "D", "cls_104"),
        ("vijayalaxmi_j", "Monday", 3, "ME", "Management & Entrepreneurship", "theory", 2, 3, "D", "cls_104"),
        ("vijayalaxmi_j", "Tuesday", 2, "ME", "Management & Entrepreneurship", "theory", 2, 3, "C", "cls_103"),
        ("vijayalaxmi_j", "Tuesday", 3, "SE&PM(D1)", "SE&PM Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("vijayalaxmi_j", "Tuesday", 4, "SE&PM(D1)", "SE&PM Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("vijayalaxmi_j", "Tuesday", 7, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "D", "cls_104"),
        ("vijayalaxmi_j", "Wednesday", 1, "SE&PM(D2)", "SE&PM Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("vijayalaxmi_j", "Wednesday", 2, "SE&PM(D2)", "SE&PM Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("vijayalaxmi_j", "Wednesday", 6, "LCS Lab(B4)", "Linux & Cloud Lab", "lab", 2, 3, "D", "cls_lab4"),
        ("vijayalaxmi_j", "Wednesday", 7, "LCS Lab(B4)", "Linux & Cloud Lab", "lab", 2, 3, "D", "cls_lab4"),
        ("vijayalaxmi_j", "Thursday", 5, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "D", "cls_104"),
        ("vijayalaxmi_j", "Friday", 1, "SE&PM(D3)", "SE&PM Laboratory", "lab", 3, 5, "D", "cls_lab2"),
        ("vijayalaxmi_j", "Friday", 2, "SE&PM(D3)", "SE&PM Laboratory", "lab", 3, 5, "D", "cls_lab2"),

        # 24. Mr. Santhosh K (3rd A & 7th C)
        ("santhosh", "Monday", 1, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "C", "cls_102"),
        ("santhosh", "Monday", 6, "GAI&PE Lab(C1)", "GAI&PE Laboratory", "lab", 4, 7, "C", "cls_lab3"),
        ("santhosh", "Monday", 7, "GAI&PE Lab(C1)", "GAI&PE Laboratory", "lab", 4, 7, "C", "cls_lab3"),
        ("santhosh", "Tuesday", 2, "OS", "Operating Systems", "theory", 2, 3, "A", "cls_101"),
        ("santhosh", "Tuesday", 5, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "C", "cls_102"),
        ("santhosh", "Tuesday", 6, "GAI&PE Lab(C2)", "GAI&PE Laboratory", "lab", 4, 7, "C", "cls_lab3"),
        ("santhosh", "Tuesday", 7, "GAI&PE Lab(C2)", "GAI&PE Laboratory", "lab", 4, 7, "C", "cls_lab3"),
        ("santhosh", "Wednesday", 2, "GAI&PE", "Generative AI & Prompt Engg", "theory", 4, 7, "C", "cls_102"),
        ("santhosh", "Wednesday", 4, "OS", "Operating Systems", "theory", 2, 3, "A", "cls_101"),
        ("santhosh", "Wednesday", 5, "GAI&PE Lab(C3)", "GAI&PE Laboratory", "lab", 4, 7, "C", "cls_lab3"),
        ("santhosh", "Wednesday", 6, "GAI&PE Lab(C3)", "GAI&PE Laboratory", "lab", 4, 7, "C", "cls_lab3"),
        ("santhosh", "Thursday", 3, "OS", "Operating Systems", "theory", 2, 3, "A", "cls_101"),

        # 25. Mrs. Shreenagamanjula Rani (1st C & 3rd B)
        ("shreenagamanjula", "Monday", 1, "DSA", "Data Structures", "theory", 2, 3, "B", "cls_102"),
        ("shreenagamanjula", "Monday", 3, "PLT", "Programming Language Tools", "theory", 1, 1, "C", "cls_103"),
        ("shreenagamanjula", "Tuesday", 4, "DSA", "Data Structures", "theory", 2, 3, "B", "cls_102"),
        ("shreenagamanjula", "Tuesday", 6, "DSA Lab(B2)", "Data Structures Lab", "lab", 2, 3, "B", "cls_lab1"),
        ("shreenagamanjula", "Tuesday", 7, "DSA Lab(B2)", "Data Structures Lab", "lab", 2, 3, "B", "cls_lab1"),
        ("shreenagamanjula", "Wednesday", 1, "DSA Lab(B3)", "Data Structures Lab", "lab", 2, 3, "B", "cls_lab1"),
        ("shreenagamanjula", "Wednesday", 2, "DSA Lab(B3)", "Data Structures Lab", "lab", 2, 3, "B", "cls_lab1"),
        ("shreenagamanjula", "Wednesday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "B", "cls_102"),
        ("shreenagamanjula", "Thursday", 2, "DSA", "Data Structures", "theory", 2, 3, "B", "cls_102"),
        ("shreenagamanjula", "Thursday", 5, "PLT", "Programming Language Tools", "theory", 1, 1, "C", "cls_103"),
        ("shreenagamanjula", "Friday", 1, "PLT", "Programming Language Tools", "theory", 1, 1, "C", "cls_103"),
        ("shreenagamanjula", "Friday", 3, "DSA Lab(B1)", "Data Structures Lab", "lab", 2, 3, "B", "cls_lab1"),
        ("shreenagamanjula", "Friday", 4, "DSA Lab(B1)", "Data Structures Lab", "lab", 2, 3, "B", "cls_lab1"),
        ("shreenagamanjula", "Friday", 5, "DSA/T", "DSA Tutorial", "theory", 2, 3, "B", "cls_102"),

        # 26. Mrs. Bhanumathi H R (3rd B & D)
        ("bhanumathi", "Monday", 3, "LD Lab(D1)", "Logic Design Lab", "lab", 2, 3, "D", "cls_lab5"),
        ("bhanumathi", "Monday", 4, "LD Lab(D1)", "Logic Design Lab", "lab", 2, 3, "D", "cls_lab5"),
        ("bhanumathi", "Tuesday", 3, "LD Lab(D2)", "Logic Design Lab", "lab", 2, 3, "D", "cls_lab5"),
        ("bhanumathi", "Tuesday", 4, "LD Lab(D2)", "Logic Design Lab", "lab", 2, 3, "D", "cls_lab5"),
        ("bhanumathi", "Tuesday", 5, "CO", "Computer Organization", "theory", 2, 3, "B", "cls_102"),
        ("bhanumathi", "Tuesday", 7, "LD", "Logic Design", "theory", 2, 3, "D", "cls_104"),
        ("bhanumathi", "Wednesday", 1, "LD", "Logic Design", "theory", 2, 3, "D", "cls_104"),
        ("bhanumathi", "Wednesday", 3, "CO", "Computer Organization", "theory", 2, 3, "B", "cls_102"),
        ("bhanumathi", "Thursday", 1, "LD Lab(D3)", "Logic Design Lab", "lab", 2, 3, "D", "cls_lab5"),
        ("bhanumathi", "Thursday", 2, "LD Lab(D3)", "Logic Design Lab", "lab", 2, 3, "D", "cls_lab5"),
        ("bhanumathi", "Friday", 1, "CO", "Computer Organization", "theory", 2, 3, "B", "cls_102"),
        ("bhanumathi", "Friday", 3, "LD", "Logic Design", "theory", 2, 3, "D", "cls_104"),

        # 27. Ms. Archana V (1st D)
        ("archana", "Monday", 4, "PLT", "Programming Language Tools", "theory", 1, 1, "D", "cls_104"),
        ("archana", "Monday", 6, "FDW Lab(B1)", "Full Stack Web Lab", "lab", 1, 1, "D", "cls_lab3"),
        ("archana", "Monday", 7, "FDW Lab(B1)", "Full Stack Web Lab", "lab", 1, 1, "D", "cls_lab3"),
        ("archana", "Tuesday", 5, "PLT Lab(D3)", "PLT Laboratory", "lab", 1, 1, "D", "cls_lab1"),
        ("archana", "Tuesday", 6, "PLT Lab(D3)", "PLT Laboratory", "lab", 1, 1, "D", "cls_lab1"),
        ("archana", "Wednesday", 3, "PLT Lab(D1)", "PLT Laboratory", "lab", 1, 1, "D", "cls_lab1"),
        ("archana", "Wednesday", 4, "PLT Lab(D1)", "PLT Laboratory", "lab", 1, 1, "D", "cls_lab1"),
        ("archana", "Wednesday", 6, "FDW Lab(B2)", "Full Stack Web Lab", "lab", 1, 1, "D", "cls_lab3"),
        ("archana", "Wednesday", 7, "FDW Lab(B2)", "Full Stack Web Lab", "lab", 1, 1, "D", "cls_lab3"),
        ("archana", "Thursday", 1, "PLT", "Programming Language Tools", "theory", 1, 1, "D", "cls_104"),
        ("archana", "Friday", 1, "PLT", "Programming Language Tools", "theory", 1, 1, "D", "cls_104"),
        ("archana", "Friday", 5, "PLT Lab(D2)", "PLT Laboratory", "lab", 1, 1, "D", "cls_lab1"),
        ("archana", "Friday", 6, "PLT Lab(D2)", "PLT Laboratory", "lab", 1, 1, "D", "cls_lab1"),

        # 28. Mrs. Ganga B M (5th D & 7th C)
        ("ganga", "Monday", 2, "LC/NC", "Linear Control / Networks", "theory", 3, 5, "D", "cls_104"),
        ("ganga", "Monday", 6, "CN", "Computer Networks", "theory", 4, 7, "C", "cls_102"),
        ("ganga", "Tuesday", 1, "LC/NC", "Linear Control / Networks", "theory", 3, 5, "D", "cls_104"),
        ("ganga", "Tuesday", 3, "CN Lab(D3)", "Computer Networks Lab", "lab", 3, 5, "D", "cls_lab4"),
        ("ganga", "Tuesday", 4, "CN Lab(D3)", "Computer Networks Lab", "lab", 3, 5, "D", "cls_lab4"),
        ("ganga", "Tuesday", 5, "CN", "Computer Networks", "theory", 4, 7, "C", "cls_102"),
        ("ganga", "Wednesday", 1, "CN Lab(D1)", "Computer Networks Lab", "lab", 3, 5, "D", "cls_lab4"),
        ("ganga", "Wednesday", 2, "CN Lab(D1)", "Computer Networks Lab", "lab", 3, 5, "D", "cls_lab4"),
        ("ganga", "Wednesday", 3, "LC/NC", "Linear Control / Networks", "theory", 3, 5, "D", "cls_104"),
        ("ganga", "Friday", 1, "CN Lab(D2)", "Computer Networks Lab", "lab", 3, 5, "D", "cls_lab4"),
        ("ganga", "Friday", 2, "CN Lab(D2)", "Computer Networks Lab", "lab", 3, 5, "D", "cls_lab4"),
        ("ganga", "Friday", 3, "CN", "Computer Networks", "theory", 4, 7, "C", "cls_102"),

        # 29. Mrs. Madhushree V (1st C & E)
        ("madhushree", "Monday", 1, "PLT Lab(C3)", "PLT Laboratory", "lab", 1, 1, "C", "cls_lab1"),
        ("madhushree", "Monday", 2, "PLT Lab(C3)", "PLT Laboratory", "lab", 1, 1, "C", "cls_lab1"),
        ("madhushree", "Monday", 3, "PLT Lab(E3)", "PLT Laboratory", "lab", 1, 1, "E", "cls_lab2"),
        ("madhushree", "Monday", 4, "PLT Lab(E3)", "PLT Laboratory", "lab", 1, 1, "E", "cls_lab2"),
        ("madhushree", "Monday", 5, "PLT", "Programming Language Tools", "theory", 1, 1, "E", "cls_104"),
        ("madhushree", "Tuesday", 2, "PLT", "Programming Language Tools", "theory", 1, 1, "E", "cls_104"),
        ("madhushree", "Tuesday", 3, "PLT Lab(C1)", "PLT Laboratory", "lab", 1, 1, "C", "cls_lab1"),
        ("madhushree", "Tuesday", 4, "PLT Lab(C1)", "PLT Laboratory", "lab", 1, 1, "C", "cls_lab1"),
        ("madhushree", "Wednesday", 1, "PLT Lab(E1)", "PLT Laboratory", "lab", 1, 1, "E", "cls_lab2"),
        ("madhushree", "Wednesday", 2, "PLT Lab(E1)", "PLT Laboratory", "lab", 1, 1, "E", "cls_lab2"),
        ("madhushree", "Thursday", 2, "PLT", "Programming Language Tools", "theory", 1, 1, "E", "cls_104"),
        ("madhushree", "Friday", 3, "PLT Lab(E2)", "PLT Laboratory", "lab", 1, 1, "E", "cls_lab2"),
        ("madhushree", "Friday", 4, "PLT Lab(E2)", "PLT Laboratory", "lab", 1, 1, "E", "cls_lab2"),
        ("madhushree", "Friday", 5, "PLT Lab(C2)", "PLT Laboratory", "lab", 1, 1, "C", "cls_lab1"),
        ("madhushree", "Friday", 6, "PLT Lab(C2)", "PLT Laboratory", "lab", 1, 1, "C", "cls_lab1"),

        # 30. Mrs. Meghana N R (1st B & 5th A)
        ("meghana", "Monday", 3, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "A", "cls_101"),
        ("meghana", "Monday", 5, "PLT Lab(B3)", "PLT Laboratory", "lab", 1, 1, "B", "cls_lab2"),
        ("meghana", "Monday", 6, "PLT Lab(B3)", "PLT Laboratory", "lab", 1, 1, "B", "cls_lab2"),
        ("meghana", "Tuesday", 1, "SE&PM Lab(A1)", "SE&PM Laboratory", "lab", 3, 5, "A", "cls_lab2"),
        ("meghana", "Tuesday", 2, "SE&PM Lab(A1)", "SE&PM Laboratory", "lab", 3, 5, "A", "cls_lab2"),
        ("meghana", "Tuesday", 7, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "A", "cls_101"),
        ("meghana", "Thursday", 1, "SE&PM Lab(A2)", "SE&PM Laboratory", "lab", 3, 5, "A", "cls_lab2"),
        ("meghana", "Thursday", 2, "SE&PM Lab(A2)", "SE&PM Laboratory", "lab", 3, 5, "A", "cls_lab2"),
        ("meghana", "Thursday", 3, "SE&PM", "Software Engg & Project Mgmt", "theory", 3, 5, "A", "cls_101"),
        ("meghana", "Thursday", 5, "PLT Lab(B1)", "PLT Laboratory", "lab", 1, 1, "B", "cls_lab2"),
        ("meghana", "Thursday", 6, "PLT Lab(B1)", "PLT Laboratory", "lab", 1, 1, "B", "cls_lab2"),
        ("meghana", "Friday", 1, "PLT Lab(B2)", "PLT Laboratory", "lab", 1, 1, "B", "cls_lab2"),
        ("meghana", "Friday", 2, "PLT Lab(B2)", "PLT Laboratory", "lab", 1, 1, "B", "cls_lab2"),
        ("meghana", "Friday", 3, "SE&PM Lab(A3)", "SE&PM Laboratory", "lab", 3, 5, "A", "cls_lab2"),
        ("meghana", "Friday", 4, "SE&PM Lab(A3)", "SE&PM Laboratory", "lab", 3, 5, "A", "cls_lab2"),

        # 31. Mrs. Manjula H S (3rd C & D, 5th B)
        ("manjula", "Monday", 1, "OS", "Operating Systems", "theory", 2, 3, "D", "cls_104"),
        ("manjula", "Monday", 6, "LCS Lab(B5)", "Linux & Cloud Lab", "lab", 2, 3, "C", "cls_lab4"),
        ("manjula", "Monday", 7, "LCS Lab(B5)", "Linux & Cloud Lab", "lab", 2, 3, "C", "cls_lab4"),
        ("manjula", "Tuesday", 3, "SE&PM Lab(B1)", "SE&PM Laboratory", "lab", 3, 5, "B", "cls_lab2"),
        ("manjula", "Tuesday", 4, "SE&PM Lab(B1)", "SE&PM Laboratory", "lab", 3, 5, "B", "cls_lab2"),
        ("manjula", "Tuesday", 7, "OS", "Operating Systems", "theory", 2, 3, "D", "cls_104"),
        ("manjula", "Wednesday", 1, "SE&PM Lab(B2)", "SE&PM Laboratory", "lab", 3, 5, "B", "cls_lab2"),
        ("manjula", "Wednesday", 2, "SE&PM Lab(B2)", "SE&PM Laboratory", "lab", 3, 5, "B", "cls_lab2"),
        ("manjula", "Wednesday", 6, "LCS Lab(B6)", "Linux & Cloud Lab", "lab", 2, 3, "C", "cls_lab4"),
        ("manjula", "Wednesday", 7, "LCS Lab(B6)", "Linux & Cloud Lab", "lab", 2, 3, "C", "cls_lab4"),
        ("manjula", "Friday", 1, "SE&PM Lab(B3)", "SE&PM Laboratory", "lab", 3, 5, "B", "cls_lab2"),
        ("manjula", "Friday", 2, "SE&PM Lab(B3)", "SE&PM Laboratory", "lab", 3, 5, "B", "cls_lab2"),
        ("manjula", "Friday", 5, "OS", "Operating Systems", "theory", 2, 3, "D", "cls_104"),

        # 32. Mrs. Suma B N (3rd A & 5th B, C & D)
        ("suma", "Monday", 6, "VCG Lab(B1)", "Visual Computing Lab", "lab", 3, 5, "B", "cls_lab5"),
        ("suma", "Monday", 7, "VCG Lab(B1)", "Visual Computing Lab", "lab", 3, 5, "B", "cls_lab5"),
        ("suma", "Tuesday", 4, "LD", "Logic Design", "theory", 2, 3, "A", "cls_101"),
        ("suma", "Tuesday", 6, "LD Lab(A1)", "Logic Design Lab", "lab", 2, 3, "A", "cls_lab5"),
        ("suma", "Tuesday", 7, "LD Lab(A1)", "Logic Design Lab", "lab", 2, 3, "A", "cls_lab5"),
        ("suma", "Wednesday", 1, "LD Lab(A2)", "Logic Design Lab", "lab", 2, 3, "A", "cls_lab5"),
        ("suma", "Wednesday", 2, "LD Lab(A2)", "Logic Design Lab", "lab", 2, 3, "A", "cls_lab5"),
        ("suma", "Wednesday", 6, "VCG Lab(B2)", "Visual Computing Lab", "lab", 3, 5, "C", "cls_lab5"),
        ("suma", "Wednesday", 7, "VCG Lab(B2)", "Visual Computing Lab", "lab", 3, 5, "C", "cls_lab5"),
        ("suma", "Thursday", 1, "LD", "Logic Design", "theory", 2, 3, "A", "cls_101"),
        ("suma", "Friday", 2, "LD", "Logic Design", "theory", 2, 3, "A", "cls_101"),
        ("suma", "Friday", 3, "LD Lab(A3)", "Logic Design Lab", "lab", 2, 3, "A", "cls_lab5"),
        ("suma", "Friday", 4, "LD Lab(A3)", "Logic Design Lab", "lab", 2, 3, "A", "cls_lab5"),

        # 33. Mrs. Prakruthi G R (5th A, B, C & D)
        ("prakruthi_gr", "Monday", 6, "CN", "Computer Networks", "theory", 3, 5, "A", "cls_101"),
        ("prakruthi_gr", "Tuesday", 1, "CN Lab(A3)", "Computer Networks Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Tuesday", 2, "CN Lab(A3)", "Computer Networks Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Tuesday", 3, "CN", "Computer Networks", "theory", 3, 5, "A", "cls_101"),
        ("prakruthi_gr", "Wednesday", 3, "CC Lab(B4)", "Cloud Computing Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Wednesday", 4, "CC Lab(B4)", "Cloud Computing Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Thursday", 1, "CN Lab(A1)", "Computer Networks Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Thursday", 2, "CN Lab(A1)", "Computer Networks Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Thursday", 6, "CC Lab(B5)", "Cloud Computing Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("prakruthi_gr", "Thursday", 7, "CC Lab(B5)", "Cloud Computing Lab", "lab", 3, 5, "B", "cls_lab4"),
        ("prakruthi_gr", "Friday", 2, "CN", "Computer Networks", "theory", 3, 5, "A", "cls_101"),
        ("prakruthi_gr", "Friday", 3, "CN Lab(A2)", "Computer Networks Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Friday", 4, "CN Lab(A2)", "Computer Networks Lab", "lab", 3, 5, "A", "cls_lab4"),
        ("prakruthi_gr", "Friday", 6, "CC Lab(B6)", "Cloud Computing Lab", "lab", 3, 5, "C", "cls_lab4"),
        ("prakruthi_gr", "Friday", 7, "CC Lab(B6)", "Cloud Computing Lab", "lab", 3, 5, "C", "cls_lab4"),
    ]

    # Map username to user_id
    user_map = {}
    cur.execute("SELECT username, id FROM users WHERE role = 'teacher'")
    for r in cur.fetchall():
        user_map[r['username']] = r['id']

    # Insert slots
    inserted_slots = 0
    for u_name, day, period, code, sub_name, stype, yr, sem, sec, rid in schedule_data:
        tid = user_map.get(u_name)
        if not tid:
            continue
        sub_id = get_or_create_sub(code, sub_name, stype, yr, sem, tid)
        tt_id = f"tt_{dept_id}_{yr}_{sem}_{sec}"

        # Clean existing slot at that exact position in that timetable
        cur.execute("DELETE FROM timetable_slots WHERE timetable_id = ? AND day = ? AND period = ?", (tt_id, day, period))
        cur.execute("""
            INSERT INTO timetable_slots (timetable_id, day, period, subject_id, teacher_id, classroom_id, slot_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tt_id, day, period, sub_id, tid, rid, stype))
        inserted_slots += 1

    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(faculty_list)} faculty members and {inserted_slots} schedule slots.")

if __name__ == '__main__':
    run_seed()
