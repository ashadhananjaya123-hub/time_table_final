"""
TimetablePro - Mutual Teacher-to-Teacher Class Swapping Engine
Handles peer-to-peer schedule exchange with strict mutual consent,
multi-point conflict validation, automatic atomic commit, audit logging,
and administrative notification dispatch.
"""

import datetime
from database import query_db, get_db_connection

def create_swap_request(sender_teacher_id, receiver_teacher_id, sender_day, sender_period,
                        receiver_day, receiver_period, sender_subject_id, receiver_subject_id, reason):
    """
    Submits a mutual class exchange request from Teacher A to Teacher B.
    Does not modify the timetable yet (requires Teacher B's explicit acceptance).
    """
    if sender_teacher_id == receiver_teacher_id:
        return {"success": False, "message": "Cannot initiate a mutual swap request with yourself."}
        
    if sender_day == receiver_day and sender_period == receiver_period:
        return {"success": False, "message": "Exchange slots cannot be at the exact same day and period."}

    # Verify sender and receiver exist
    sender = query_db("SELECT id, name, role FROM users WHERE id = ?", (sender_teacher_id,), one=True)
    receiver = query_db("SELECT id, name, role FROM users WHERE id = ?", (receiver_teacher_id,), one=True)
    
    if not sender or not receiver or sender['role'] != 'teacher' or receiver['role'] != 'teacher':
        return {"success": False, "message": "Invalid faculty participant specified for swap."}

    req_id = f"swap_{int(datetime.datetime.now().timestamp() * 1000)}"
    now = datetime.datetime.now().isoformat()
    
    query_db(
        """
        INSERT INTO swap_requests (
            id, sender_teacher_id, receiver_teacher_id,
            sender_day, sender_period, sender_subject_id,
            receiver_day, receiver_period, receiver_subject_id,
            reason, status, admin_notified, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)
        """,
        (
            req_id, sender_teacher_id, receiver_teacher_id,
            sender_day, sender_period, sender_subject_id,
            receiver_day, receiver_period, receiver_subject_id,
            reason, now, now
        ),
        commit=True
    )
    
    # Notify Receiver Teacher
    sub_send = query_db("SELECT name, code FROM subjects WHERE id = ?", (sender_subject_id,), one=True)
    sub_send_title = sub_send['code'] if sub_send else "Class"
    
    notif_id = f"not_{int(datetime.datetime.now().timestamp() * 1000)}"
    query_db(
        """
        INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at)
        VALUES (?, ?, 'teacher', ?, ?, '/teacher#swaps', 0, ?)
        """,
        (
            notif_id, receiver_teacher_id,
            "Incoming Class Swap Proposal",
            f"{sender['name']} proposed exchanging {sender_day} Period {sender_period} ({sub_send_title}) for your {receiver_day} Period {receiver_period}.",
            now
        ),
        commit=True
    )
    
    return {"success": True, "request_id": req_id, "message": "Swap proposal dispatched to colleague for approval."}

def process_swap_decision(swap_id, responder_teacher_id, action, rejection_reason=None):
    """
    Processes Teacher B's response (accept or reject).
    If accepted:
    - Runs complete collision validation across all timetables
    - Executes atomic swap in the database
    - Logs to swap_history
    - Notifies both teachers and the Administrator
    """
    swap = query_db("SELECT * FROM swap_requests WHERE id = ?", (swap_id,), one=True)
    if not swap:
        return {"success": False, "message": "Swap request not found."}
        
    if swap['status'] != 'pending':
        return {"success": False, "message": f"This swap request has already been {swap['status']}."}
        
    if swap['receiver_teacher_id'] != responder_teacher_id:
        return {"success": False, "message": "Only the recipient faculty member can respond to this proposal."}

    now = datetime.datetime.now().isoformat()
    sender = query_db("SELECT id, name FROM users WHERE id = ?", (swap['sender_teacher_id'],), one=True)
    receiver = query_db("SELECT id, name FROM users WHERE id = ?", (swap['receiver_teacher_id'],), one=True)

    if action == 'reject':
        query_db(
            "UPDATE swap_requests SET status = 'rejected', updated_at = ? WHERE id = ?",
            (now, swap_id), commit=True
        )
        
        # Notify sender
        notif_msg = f"{receiver['name']} declined your class swap proposal for {swap['sender_day']} Period {swap['sender_period']}."
        if rejection_reason:
            notif_msg += f" Note: {rejection_reason}"
            
        query_db(
            "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, ?, 'teacher', ?, ?, '/teacher#swaps', 0, ?)",
            (f"not_{int(datetime.datetime.now().timestamp()*1000)}", swap['sender_teacher_id'], "Swap Proposal Declined", notif_msg, now),
            commit=True
        )
        return {"success": True, "message": "Swap proposal declined."}

    # ACTION == 'ACCEPT'
    # 1. Locate the two timetable slot records
    sender_slot = query_db(
        "SELECT * FROM timetable_slots WHERE teacher_id = ? AND day = ? AND period = ?",
        (swap['sender_teacher_id'], swap['sender_day'], swap['sender_period']),
        one=True
    )
    receiver_slot = query_db(
        "SELECT * FROM timetable_slots WHERE teacher_id = ? AND day = ? AND period = ?",
        (swap['receiver_teacher_id'], swap['receiver_day'], swap['receiver_period']),
        one=True
    )
    
    if not sender_slot or not receiver_slot:
        return {
            "success": False,
            "message": "Validation Failure: One or both of the target timetable slots no longer exist."
        }

    # 2. Collision Validation
    # Check if Teacher A is already teaching elsewhere at receiver_day, receiver_period
    collision_a = query_db(
        "SELECT id FROM timetable_slots WHERE teacher_id = ? AND day = ? AND period = ? AND id != ?",
        (swap['sender_teacher_id'], swap['receiver_day'], swap['receiver_period'], sender_slot['id']),
        one=True
    )
    if collision_a:
        return {
            "success": False,
            "message": f"Conflict detected: {sender['name']} is already scheduled for another class on {swap['receiver_day']} Period {swap['receiver_period']}."
        }
        
    # Check if Teacher B is already teaching elsewhere at sender_day, sender_period
    collision_b = query_db(
        "SELECT id FROM timetable_slots WHERE teacher_id = ? AND day = ? AND period = ? AND id != ?",
        (swap['receiver_teacher_id'], swap['sender_day'], swap['sender_period'], receiver_slot['id']),
        one=True
    )
    if collision_b:
        return {
            "success": False,
            "message": f"Conflict detected: {receiver['name']} is already scheduled for another class on {swap['sender_day']} Period {swap['sender_period']}."
        }

    # 3. Atomic Timetable Swap Execution
    conn, db_type = get_db_connection()
    try:
        cur = conn.cursor()
        
        # If both slots belong to the same timetable/cohort, we swap their day & period
        if sender_slot['timetable_id'] == receiver_slot['timetable_id']:
            cur.execute(
                "UPDATE timetable_slots SET day = ?, period = ? WHERE id = ?",
                (swap['receiver_day'], swap['receiver_period'], sender_slot['id'])
            )
            cur.execute(
                "UPDATE timetable_slots SET day = ?, period = ? WHERE id = ?",
                (swap['sender_day'], swap['sender_period'], receiver_slot['id'])
            )
        else:
            # Different timetables: swap the assigned teacher and subject between the two slots
            # Slot A gets Teacher B & Subject B
            cur.execute(
                "UPDATE timetable_slots SET teacher_id = ?, subject_id = ? WHERE id = ?",
                (swap['receiver_teacher_id'], receiver_slot['subject_id'], sender_slot['id'])
            )
            # Slot B gets Teacher A & Subject A
            cur.execute(
                "UPDATE timetable_slots SET teacher_id = ?, subject_id = ? WHERE id = ?",
                (swap['sender_teacher_id'], sender_slot['subject_id'], receiver_slot['id'])
            )

        # Mark swap request as accepted
        cur.execute(
            "UPDATE swap_requests SET status = 'accepted', admin_notified = 1, updated_at = ? WHERE id = ?",
            (now, swap_id)
        )
        
        # Log to immutable swap history
        details = (
            f"Mutual swap executed between {sender['name']} and {receiver['name']}. "
            f"Exchanged ({swap['sender_day']} Period {swap['sender_period']}) with "
            f"({swap['receiver_day']} Period {swap['receiver_period']}). Reason: {swap['reason']}"
        )
        cur.execute(
            "INSERT INTO swap_history (swap_request_id, sender_name, receiver_name, details, executed_at) VALUES (?, ?, ?, ?, ?)",
            (swap_id, sender['name'], receiver['name'], details, now)
        )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"Database transaction failed: {str(e)}"}
    finally:
        conn.close()

    # 4. Dispatch Notifications
    # To Sender Teacher
    query_db(
        "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, ?, 'teacher', ?, ?, '/teacher#timetable', 0, ?)",
        (
            f"not_{int(datetime.datetime.now().timestamp()*1000)}_1",
            swap['sender_teacher_id'],
            "Mutual Swap Confirmed & Applied",
            f"Your class swap with {receiver['name']} was confirmed. Your timetable has been automatically updated.",
            now
        ),
        commit=True
    )
    # To Receiver Teacher
    query_db(
        "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, ?, 'teacher', ?, ?, '/teacher#timetable', 0, ?)",
        (
            f"not_{int(datetime.datetime.now().timestamp()*1000)}_2",
            swap['receiver_teacher_id'],
            "Mutual Swap Confirmed & Applied",
            f"Class swap with {sender['name']} finalized. Timetable schedule updated.",
            now
        ),
        commit=True
    )
    # To Administrator
    admin = query_db("SELECT id FROM users WHERE role = 'admin' LIMIT 1", one=True)
    if admin:
        query_db(
            "INSERT INTO notifications (id, user_id, user_role, title, message, link, is_read, created_at) VALUES (?, ?, 'admin', ?, ?, '/admin#swaps', 0, ?)",
            (
                f"not_{int(datetime.datetime.now().timestamp()*1000)}_3",
                admin['id'],
                "Faculty Mutual Class Swap Completed",
                f"{sender['name']} and {receiver['name']} successfully exchanged classes for {swap['sender_day']} P{swap['sender_period']} and {swap['receiver_day']} P{swap['receiver_period']}.",
                now
            ),
            commit=True
        )

    return {"success": True, "message": "Mutual swap confirmed, timetable updated, and audit logged."}
