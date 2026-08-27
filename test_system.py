import unittest
from app import create_app
from models import db, User, Exam, Question, Option, ExamAttempt, StudentAnswer

class SystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_user_authentication(self):
        """Test login with student and admin accounts and password hashing."""
        with self.app.app_context():
            admin = User.query.filter_by(email='admin@college.edu').first()
            self.assertIsNotNone(admin)
            self.assertTrue(admin.check_password('Admin@123'))
            self.assertFalse(admin.check_password('WrongPass'))
            self.assertTrue(admin.is_admin)

            student = User.query.filter_by(register_no='2024CS001').first()
            self.assertIsNotNone(student)
            self.assertTrue(student.check_password('Student@123'))
            self.assertFalse(student.is_admin)

    def test_02_login_and_role_redirect(self):
        """Test login endpoint and redirection based on role."""
        # Admin login
        res = self.client.post('/login', data={
            'login_id': 'admin@college.edu',
            'password': 'Admin@123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/dashboard', res.headers['Location'])

        # Log out
        self.client.get('/logout')

        # Student login
        res2 = self.client.post('/login', data={
            'login_id': '2024CS001',
            'password': 'Student@123'
        }, follow_redirects=False)
        self.assertEqual(res2.status_code, 302)
        self.assertIn('/student/dashboard', res2.headers['Location'])

    def test_03_role_authorization_security(self):
        """Test that students cannot access admin pages."""
        with self.client:
            # Log in as student
            self.client.post('/login', data={'login_id': '2024CS001', 'password': 'Student@123'})
            # Attempt to access admin dashboard
            res = self.client.get('/admin/dashboard', follow_redirects=False)
            self.assertEqual(res.status_code, 302)
            self.assertIn('/student/dashboard', res.headers['Location'])

    def test_04_exam_data_integrity(self):
        """Verify exams, questions, and options are properly seeded."""
        with self.app.app_context():
            exams = Exam.query.all()
            self.assertGreaterEqual(len(exams), 3)
            for ex in exams:
                self.assertGreaterEqual(len(ex.questions), 5)
                for q in ex.questions:
                    self.assertEqual(len(q.options), 4)
                    correct_opts = [opt for opt in q.options if opt.is_correct]
                    self.assertEqual(len(correct_opts), 1)

    def test_05_student_performance_calculation(self):
        """Test computation of student performance metrics and progression deltas."""
        with self.app.app_context():
            student = User.query.filter_by(register_no='2024CS001').first()
            attempts = ExamAttempt.query.filter_by(user_id=student.id, status='completed').all()
            self.assertGreaterEqual(len(attempts), 3)

            # Test response of student performance page
            with self.client:
                self.client.post('/login', data={'login_id': '2024CS001', 'password': 'Student@123'})
                res = self.client.get('/student/performance')
                self.assertEqual(res.status_code, 200)
                self.assertIn(b'Student Performance Analytics', res.data)
                self.assertIn(b'Previous vs Current Score Comparison', res.data)

                # Test report card page
                rc_res = self.client.get('/student/report-card')
                self.assertEqual(rc_res.status_code, 200)
                self.assertIn(b'OFFICIAL STUDENT GRADE REPORT', rc_res.data)

    def test_06_admin_export_csv(self):
        """Test admin results CSV export endpoint."""
        with self.client:
            self.client.post('/login', data={'login_id': 'admin@college.edu', 'password': 'Admin@123'})
            res = self.client.get('/admin/results/export-csv')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.mimetype, 'text/csv')
            self.assertIn(b'Register Number', res.data)

if __name__ == '__main__':
    unittest.main()
