"""
TimetablePro - End-to-End System Test Suite
Executes automated test cases across all modules and APIs:
- Authentication & RBAC
- Admin Stats & Directories
- Automatic Timetable Generation & Publishing
- Teacher-to-Teacher Mutual Class Swapping Workflow
- Faculty Utilization & Workload Analytics
- Syllabus Progress & Assignment Submission
- Events, Lost-Class Recovery & Activities
- Master Calendar Events Feed
"""

import unittest
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from database import query_db

class TimetableProTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.client.testing = True

    def test_01_root_and_login_page(self):
        """Test root redirect and login page accessibility"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        res_login = self.client.get('/login')
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'TimetablePro', res_login.data)
        self.assertIn(b'Administrator', res_login.data)

    def test_02_authentication_and_rbac(self):
        """Test login for admin, teacher, student, and invalid credentials"""
        # Invalid password
        res_fail = self.client.post('/api/auth/login', json={
            'username': 'admin', 'password': 'wrongpassword', 'role': 'admin'
        })
        self.assertEqual(res_fail.status_code, 401)
        self.assertFalse(res_fail.get_json()['success'])

        # Successful Admin login
        res_adm = self.client.post('/api/auth/login', json={
            'username': 'admin', 'password': 'admin123', 'role': 'admin'
        })
        self.assertEqual(res_adm.status_code, 200)
        self.assertTrue(res_adm.get_json()['success'])

        # Check me
        res_me = self.client.get('/api/auth/me')
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.get_json()['user']['role'], 'admin')

        # Logout
        self.client.get('/api/auth/logout')
        res_logged_out = self.client.get('/api/auth/me')
        self.assertEqual(res_logged_out.status_code, 401)

    def test_03_admin_stats_and_directories(self):
        """Test admin dashboard statistics and faculty directory"""
        # Login as admin
        self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'admin'})

        res_stats = self.client.get('/api/admin/stats')
        self.assertEqual(res_stats.status_code, 200)
        data = res_stats.get_json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['counts']['teachers'], 12)
        self.assertGreaterEqual(data['counts']['departments'], 3)
        self.assertGreaterEqual(data['counts']['subjects'], 20)

        # Teachers directory
        res_tch = self.client.get('/api/teachers')
        self.assertEqual(res_tch.status_code, 200)
        self.assertGreaterEqual(len(res_tch.get_json()['teachers']), 12)

        # Students directory
        res_stu = self.client.get('/api/students')
        self.assertEqual(res_stu.status_code, 200)
        self.assertGreaterEqual(len(res_stu.get_json()['students']), 5)

    def test_04_timetable_generation_and_publishing(self):
        """Test automatic timetable generation for CSE Year 1 Semester 2 and publish"""
        self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'admin'})

        # Generate for CSE Y1 S2
        res_gen = self.client.post('/api/timetables/generate', json={
            'department_id': 'dept_1',
            'year': 1,
            'semester': 2
        })
        self.assertEqual(res_gen.status_code, 200)
        gen_data = res_gen.get_json()
        self.assertTrue(gen_data['success'])
        tt_id = gen_data['timetable_id']

        # Verify slots were created
        res_tt = self.client.get(f'/api/timetables?department_id=dept_1&year=1&semester=2')
        self.assertEqual(res_tt.status_code, 200)
        slots = res_tt.get_json()['slots']
        self.assertGreater(len(slots), 10)

        # Publish timetable
        res_pub = self.client.post(f'/api/timetables/{tt_id}/publish')
        self.assertEqual(res_pub.status_code, 200)
        self.assertTrue(res_pub.get_json()['success'])

    def test_05_mutual_teacher_swapping_workflow(self):
        """Test peer-to-peer mutual class swapping workflow"""
        # Step 1: Login as Teacher 1 (Dr. Rajesh Kumar)
        self.client.post('/api/auth/login', json={'username': 'rajesh', 'password': 'teacher123', 'role': 'teacher'})

        # Dynamically select a valid, non-colliding pair of slots for Dr. Rajesh (tch_1) and Prof. Sneha (tch_2)
        slots_t1 = query_db("SELECT * FROM timetable_slots WHERE teacher_id = 'tch_1' AND slot_type = 'regular'")
        slots_t2 = query_db("SELECT * FROM timetable_slots WHERE teacher_id = 'tch_2' AND slot_type = 'regular'")
        valid_pair = None
        for s1 in slots_t1:
            for s2 in slots_t2:
                if s1['day'] == s2['day'] and s1['period'] == s2['period']:
                    continue
                busy_t1 = query_db("SELECT id FROM timetable_slots WHERE teacher_id = 'tch_1' AND day = ? AND period = ? AND id != ?", (s2['day'], s2['period'], s1['id']), one=True)
                busy_t2 = query_db("SELECT id FROM timetable_slots WHERE teacher_id = 'tch_2' AND day = ? AND period = ? AND id != ?", (s1['day'], s1['period'], s2['id']), one=True)
                if not busy_t1 and not busy_t2:
                    valid_pair = (s1, s2)
                    break
            if valid_pair:
                break
        
        self.assertIsNotNone(valid_pair, "A valid non-conflicting slot pair should exist for testing swap")
        slot1, slot2 = valid_pair

        # Submit swap proposal to Teacher 2 (Prof. Sneha Iyer)
        res_prop = self.client.post('/api/swaps/request', json={
            'receiver_teacher_id': 'tch_2',
            'sender_day': slot1['day'],
            'sender_period': slot1['period'],
            'sender_subject_id': slot1['subject_id'],
            'receiver_day': slot2['day'],
            'receiver_period': slot2['period'],
            'receiver_subject_id': slot2['subject_id'],
            'reason': 'Automated test mutual exchange.'
        })
        self.assertEqual(res_prop.status_code, 200)
        swap_id = res_prop.get_json()['request_id']

        # Step 2: Login as Teacher 2 and inspect incoming proposal
        self.client.post('/api/auth/login', json={'username': 'sneha', 'password': 'teacher123', 'role': 'teacher'})
        res_swaps = self.client.get('/api/swaps')
        self.assertEqual(res_swaps.status_code, 200)
        incoming = res_swaps.get_json()['incoming']
        target_swap = next((s for s in incoming if s['id'] == swap_id), None)
        self.assertIsNotNone(target_swap)
        self.assertEqual(target_swap['status'], 'pending')

        # Step 3: Teacher 2 accepts swap
        res_accept = self.client.post('/api/swaps/respond', json={
            'swap_id': swap_id,
            'action': 'accept'
        })
        self.assertEqual(res_accept.status_code, 200)
        self.assertTrue(res_accept.get_json()['success'])

        # Verify audit history
        res_history = self.client.get('/api/swaps')
        history = res_history.get_json()['history']
        self.assertGreater(len(history), 0)

    def test_06_workload_analytics(self):
        """Test workload calculation engine and Chart.js payloads"""
        self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'admin'})
        res = self.client.get('/api/analytics/workload')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()['analytics']
        self.assertIn('faculty_metrics', data)
        self.assertIn('charts', data)
        self.assertIn('bar', data['charts'])
        self.assertIn('doughnut', data['charts'])
        self.assertGreater(data['summary']['total_assigned_periods'], 0)

    def test_07_syllabus_and_assignments(self):
        """Test syllabus topic tracking and student assignment submission"""
        # Teacher adds syllabus topic
        self.client.post('/api/auth/login', json={'username': 'rajesh', 'password': 'teacher123', 'role': 'teacher'})
        res_topic = self.client.post('/api/syllabus', json={
            'subject_id': 'sub_1',
            'title': 'Test Syllabus Topic: Red-Black Trees',
            'chapter': 'Module 5',
            'notes': 'Self-balancing properties'
        })
        self.assertEqual(res_topic.status_code, 200)

        # Verify syllabus stats
        res_syl = self.client.get('/api/syllabus/sub_1')
        self.assertEqual(res_syl.status_code, 200)
        stats = res_syl.get_json()['stats']
        self.assertGreater(stats['total'], 0)

        # Student submits assignment
        self.client.post('/api/auth/login', json={'username': 'amit', 'password': 'student123', 'role': 'student'})
        res_subm = self.client.post('/api/student/assignments/asn_1/submit', json={
            'notes': 'Verified test suite submission.'
        })
        self.assertEqual(res_subm.status_code, 200)

    def test_08_calendar_feed(self):
        """Test FullCalendar events feed"""
        self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123', 'role': 'admin'})
        res_cal = self.client.get('/api/calendar/events')
        self.assertEqual(res_cal.status_code, 200)
        events = res_cal.get_json()
        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)

if __name__ == '__main__':
    unittest.main()
