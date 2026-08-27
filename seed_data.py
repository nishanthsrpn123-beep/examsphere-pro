from datetime import datetime, timedelta
from app import create_app
from models import db, User, Exam, Question, Option, ExamAttempt, StudentAnswer

def seed_database():
    app = create_app()
    with app.app_context():
        print("Clearing existing tables and creating fresh schema...")
        db.drop_all()
        db.create_all()

        print("Seeding Admin user...")
        admin = User(
            register_no="ADMIN001",
            full_name="Dr. S. K. Narayanan (Exam Controller)",
            email="admin@college.edu",
            role="admin",
            department="Academic Administration",
            semester=0
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()

        print("Seeding Students...")
        students_data = [
            ("2024CS001", "Rahul Sharma", "rahul@college.edu", "Computer Science & Engineering", 6),
            ("2024CS002", "Priya Patel", "priya@college.edu", "Computer Science & Engineering", 6),
            ("2024CS003", "Amit Kumar", "amit@college.edu", "Computer Science & Engineering", 6),
            ("2024IT004", "Sneha Reddy", "sneha@college.edu", "Information Technology", 6),
            ("2024EC005", "Vikram Singh", "vikram@college.edu", "Electronics & Communication", 6)
        ]

        student_objs = []
        for reg, name, email, dept, sem in students_data:
            s = User(
                register_no=reg,
                full_name=name,
                email=email,
                role="student",
                department=dept,
                semester=sem
            )
            s.set_password("Student@123")
            db.session.add(s)
            student_objs.append(s)
        
        db.session.commit()

        print("Seeding Exams and Question Banks...")
        
        # 1. Mathematics
        math_exam = Exam(
            title="Engineering Mathematics & Statistical Analysis",
            course_code="MATH301",
            description="Covers linear algebra, probability distributions, calculus, matrices, and statistical hypotheses testing.",
            duration_minutes=25,
            pass_percentage=40.0,
            is_active=True,
            created_by=admin.id
        )
        db.session.add(math_exam)
        db.session.flush()

        math_questions = [
            {
                "text": "What is the determinant of a 2x2 matrix [[3, 2], [1, 4]]?",
                "marks": 2.0,
                "explanation": "Determinant = (ad - bc) = (3*4 - 2*1) = 12 - 2 = 10.",
                "options": [
                    ("A", "10", True),
                    ("B", "14", False),
                    ("C", "8", False),
                    ("D", "-10", False)
                ]
            },
            {
                "text": "If a fair 6-sided die is rolled twice, what is the probability of obtaining a sum of 7?",
                "marks": 2.0,
                "explanation": "Favorable outcomes are (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) = 6 pairs. Total pairs = 36. Probability = 6/36 = 1/6.",
                "options": [
                    ("A", "1/12", False),
                    ("B", "1/6", True),
                    ("C", "7/36", False),
                    ("D", "1/36", False)
                ]
            },
            {
                "text": "What is the derivative of f(x) = x * ln(x) with respect to x?",
                "marks": 2.0,
                "explanation": "Using product rule: d/dx(x * ln(x)) = (1)*ln(x) + x*(1/x) = ln(x) + 1.",
                "options": [
                    ("A", "ln(x)", False),
                    ("B", "1/x", False),
                    ("C", "ln(x) + 1", True),
                    ("D", "x + ln(x)", False)
                ]
            },
            {
                "text": "What is the mean of the dataset: 4, 8, 6, 5, 3, 10, 6?",
                "marks": 2.0,
                "explanation": "Sum = 4 + 8 + 6 + 5 + 3 + 10 + 6 = 42. Count = 7. Mean = 42 / 7 = 6.",
                "options": [
                    ("A", "5.5", False),
                    ("B", "6.0", True),
                    ("C", "6.5", False),
                    ("D", "7.0", False)
                ]
            },
            {
                "text": "For two events A and B, if P(A)=0.4, P(B)=0.5 and P(A ∩ B)=0.2, what is P(A ∪ B)?",
                "marks": 2.0,
                "explanation": "P(A ∪ B) = P(A) + P(B) - P(A ∩ B) = 0.4 + 0.5 - 0.2 = 0.7.",
                "options": [
                    ("A", "0.7", True),
                    ("B", "0.9", False),
                    ("C", "0.6", False),
                    ("D", "0.8", False)
                ]
            },
            {
                "text": "Which property indicates that matrix multiplication is NOT generally commutative?",
                "marks": 2.0,
                "explanation": "For matrices A and B, in general AB ≠ BA, meaning matrix multiplication is non-commutative.",
                "options": [
                    ("A", "A(B + C) = AB + AC", False),
                    ("B", "AB = BA", False),
                    ("C", "AB ≠ BA in general", True),
                    ("D", "(AB)C = A(BC)", False)
                ]
            }
        ]

        math_q_objs = []
        for q_data in math_questions:
            q = Question(exam_id=math_exam.id, question_text=q_data["text"], marks=q_data["marks"], explanation=q_data["explanation"])
            db.session.add(q)
            db.session.flush()
            math_q_objs.append(q)
            for opt_label, opt_text, is_corr in q_data["options"]:
                opt = Option(question_id=q.id, option_label=opt_label, option_text=opt_text, is_correct=is_corr)
                db.session.add(opt)

        # 2. Python Programming
        python_exam = Exam(
            title="Python Programming & Data Structures",
            course_code="CS302",
            description="Covers Python fundamentals, OOP concepts, list comprehensions, time complexity, dictionaries, and recursion.",
            duration_minutes=30,
            pass_percentage=40.0,
            is_active=True,
            created_by=admin.id
        )
        db.session.add(python_exam)
        db.session.flush()

        python_questions = [
            {
                "text": "What will be the output of `print(type([1, 2, (3, 4)]))` in Python 3?",
                "marks": 2.0,
                "explanation": "The outermost container is square brackets [], which denotes a `list`.",
                "options": [
                    ("A", "<class 'tuple'>", False),
                    ("B", "<class 'list'>", True),
                    ("C", "<class 'dict'>", False),
                    ("D", "<class 'set'>", False)
                ]
            },
            {
                "text": "What is the average time complexity of searching a key in a Python dictionary?",
                "marks": 2.0,
                "explanation": "Python dictionaries are implemented using hash tables, giving average O(1) lookup time complexity.",
                "options": [
                    ("A", "O(1)", True),
                    ("B", "O(log n)", False),
                    ("C", "O(n)", False),
                    ("D", "O(n log n)", False)
                ]
            },
            {
                "text": "Which keyword is used to define an anonymous function in Python?",
                "marks": 2.0,
                "explanation": "Anonymous functions without standard `def` names are created using the `lambda` keyword.",
                "options": [
                    ("A", "def", False),
                    ("B", "func", False),
                    ("C", "anonymous", False),
                    ("D", "lambda", True)
                ]
            },
            {
                "text": "What is the result of `[x**2 for x in range(5) if x % 2 == 0]`?",
                "marks": 2.0,
                "explanation": "Range(5) yields 0, 1, 2, 3, 4. Even numbers are 0, 2, 4. Their squares are 0, 4, 16 -> [0, 4, 16].",
                "options": [
                    ("A", "[0, 4, 16]", True),
                    ("B", "[1, 9]", False),
                    ("C", "[0, 1, 4, 9, 16]", False),
                    ("D", "[4, 16]", False)
                ]
            },
            {
                "text": "In Python OOP, what does the `__init__` method represent?",
                "marks": 2.0,
                "explanation": "`__init__` is the constructor method automatically invoked when a new instance of a class is created.",
                "options": [
                    ("A", "Class Destructor", False),
                    ("B", "Instance Initializer / Constructor", True),
                    ("C", "Static Method Decorator", False),
                    ("D", "Garbage Collector", False)
                ]
            },
            {
                "text": "How do you handle potential exceptions when opening and reading a file in Python safely?",
                "marks": 2.0,
                "explanation": "The `try ... except ... finally` block (or `with open(...)`) ensures proper exception handling and resource closure.",
                "options": [
                    ("A", "catch ... throw block", False),
                    ("B", "try ... except block", True),
                    ("C", "if error ... else block", False),
                    ("D", "test ... verify block", False)
                ]
            }
        ]

        python_q_objs = []
        for q_data in python_questions:
            q = Question(exam_id=python_exam.id, question_text=q_data["text"], marks=q_data["marks"], explanation=q_data["explanation"])
            db.session.add(q)
            db.session.flush()
            python_q_objs.append(q)
            for opt_label, opt_text, is_corr in q_data["options"]:
                opt = Option(question_id=q.id, option_label=opt_label, option_text=opt_text, is_correct=is_corr)
                db.session.add(opt)

        # 3. Database Management Systems
        db_exam = Exam(
            title="Database Management Systems (DBMS) & SQL",
            course_code="CS305",
            description="Covers relational algebra, ACID properties, normalization (1NF to BCNF), indexing, and SQL queries.",
            duration_minutes=25,
            pass_percentage=40.0,
            is_active=True,
            created_by=admin.id
        )
        db.session.add(db_exam)
        db.session.flush()

        db_questions = [
            {
                "text": "Which ACID property guarantees that all operations in a database transaction either complete fully or none at all?",
                "marks": 2.0,
                "explanation": "Atomicity ensures 'all-or-nothing' execution of database transactions.",
                "options": [
                    ("A", "Atomicity", True),
                    ("B", "Consistency", False),
                    ("C", "Isolation", False),
                    ("D", "Durability", False)
                ]
            },
            {
                "text": "Which normal form removes partial functional dependencies where non-prime attributes depend on a part of candidate key?",
                "marks": 2.0,
                "explanation": "Second Normal Form (2NF) requires 1NF and no partial dependencies on any candidate key.",
                "options": [
                    ("A", "1NF", False),
                    ("B", "2NF", True),
                    ("C", "3NF", False),
                    ("D", "BCNF", False)
                ]
            },
            {
                "text": "Which SQL clause is used to filter groups created by the `GROUP BY` clause?",
                "marks": 2.0,
                "explanation": "The `HAVING` clause is specifically designed to filter aggregated rows produced by GROUP BY.",
                "options": [
                    ("A", "WHERE", False),
                    ("B", "HAVING", True),
                    ("C", "FILTER", False),
                    ("D", "ORDER BY", False)
                ]
            },
            {
                "text": "What type of JOIN returns all records from the left table, and the matched records from the right table?",
                "marks": 2.0,
                "explanation": "A LEFT OUTER JOIN returns all tuples from the left relation, filling missing right relation attributes with NULL.",
                "options": [
                    ("A", "INNER JOIN", False),
                    ("B", "RIGHT JOIN", False),
                    ("C", "LEFT JOIN", True),
                    ("D", "FULL JOIN", False)
                ]
            },
            {
                "text": "Which SQL command is classified as Data Definition Language (DDL)?",
                "marks": 2.0,
                "explanation": "TRUNCATE, CREATE, ALTER, and DROP are DDL commands that modify schema structures.",
                "options": [
                    ("A", "SELECT", False),
                    ("B", "INSERT", False),
                    ("C", "UPDATE", False),
                    ("D", "TRUNCATE", True)
                ]
            },
            {
                "text": "What data structure is most commonly utilized in RDBMS indexing for fast range searches and lookups?",
                "marks": 2.0,
                "explanation": "B+ Trees provide balanced depth, high fan-out, and linked leaf nodes ideal for fast range scans and equality lookups.",
                "options": [
                    ("A", "B+ Tree", True),
                    ("B", "Binary Search Tree", False),
                    ("C", "Linked List", False),
                    ("D", "Heap", False)
                ]
            }
        ]

        db_q_objs = []
        for q_data in db_questions:
            q = Question(exam_id=db_exam.id, question_text=q_data["text"], marks=q_data["marks"], explanation=q_data["explanation"])
            db.session.add(q)
            db.session.flush()
            db_q_objs.append(q)
            for opt_label, opt_text, is_corr in q_data["options"]:
                opt = Option(question_id=q.id, option_label=opt_label, option_text=opt_text, is_correct=is_corr)
                db.session.add(opt)

        db.session.commit()

        print("Seeding Sample Student Attempts and Scores for Performance Analysis...")
        
        # Helper to simulate a submitted attempt
        def record_attempt(student, exam, attempt_num, correct_indices, days_ago, time_secs):
            q_list = list(exam.questions)
            max_sc = sum(q.marks for q in q_list)
            tot_sc = 0.0
            
            att_time = datetime.utcnow() - timedelta(days=days_ago)
            attempt = ExamAttempt(
                user_id=student.id,
                exam_id=exam.id,
                attempt_number=attempt_num,
                start_time=att_time - timedelta(seconds=time_secs),
                submitted_at=att_time,
                time_taken_seconds=time_secs,
                status='completed'
            )
            db.session.add(attempt)
            db.session.flush()

            for idx, q in enumerate(q_list):
                opts = list(q.options)
                corr_opt = next((o for o in opts if o.is_correct), None)
                incorr_opt = next((o for o in opts if not o.is_correct), None)

                if idx in correct_indices:
                    sel_opt = corr_opt
                    is_c = True
                    marks = q.marks
                    tot_sc += marks
                else:
                    sel_opt = incorr_opt
                    is_c = False
                    marks = 0.0

                ans = StudentAnswer(
                    attempt_id=attempt.id,
                    question_id=q.id,
                    selected_option_id=sel_opt.id if sel_opt else None,
                    is_correct=is_c,
                    marks_awarded=marks
                )
                db.session.add(ans)

            attempt.total_score = tot_sc
            attempt.max_score = max_sc
            attempt.percentage = round((tot_sc / max_sc) * 100.0, 2) if max_sc > 0 else 0.0
            return attempt

        # Student 1: Rahul Sharma (2024CS001) - Demonstrates progress across multiple attempts
        # Math Attempt 1 (10 days ago): 3/6 correct (50.0%)
        record_attempt(student_objs[0], math_exam, 1, [0, 1, 2], 10, 950)
        # Math Attempt 2 (3 days ago): 5/6 correct (83.33%) -> High improvement!
        record_attempt(student_objs[0], math_exam, 2, [0, 1, 2, 3, 4], 3, 780)
        # Python Attempt 1 (7 days ago): 5/6 correct (83.33%)
        record_attempt(student_objs[0], python_exam, 1, [0, 1, 2, 4, 5], 7, 840)
        # Python Attempt 2 (1 day ago): 6/6 correct (100%)
        record_attempt(student_objs[0], python_exam, 2, [0, 1, 2, 3, 4, 5], 1, 620)
        # DBMS Attempt 1 (4 days ago): 4/6 correct (66.67%)
        record_attempt(student_objs[0], db_exam, 1, [0, 1, 2, 3], 4, 710)

        # Student 2: Priya Patel (2024CS002) - Consistently high performer
        record_attempt(student_objs[1], math_exam, 1, [0, 1, 2, 3, 4, 5], 8, 600)  # 100%
        record_attempt(student_objs[1], python_exam, 1, [0, 1, 2, 3, 4, 5], 6, 540) # 100%
        record_attempt(student_objs[1], db_exam, 1, [0, 1, 2, 3, 4], 2, 610)        # 83.33%

        # Student 3: Amit Kumar (2024CS003) - Steady mid-tier performer
        record_attempt(student_objs[2], math_exam, 1, [0, 2, 4], 9, 1100)           # 50%
        record_attempt(student_objs[2], python_exam, 1, [1, 2, 3, 4], 5, 890)       # 66.67%
        record_attempt(student_objs[2], db_exam, 1, [0, 1, 4, 5], 2, 920)           # 66.67%

        # Student 4: Sneha Reddy (2024IT004) - High in Python & DBMS
        record_attempt(student_objs[3], math_exam, 1, [0, 1, 3], 7, 1020)           # 50%
        record_attempt(student_objs[3], python_exam, 1, [0, 1, 2, 3, 5], 4, 680)    # 83.33%
        record_attempt(student_objs[3], db_exam, 1, [0, 1, 2, 3, 4, 5], 1, 590)    # 100%

        # Student 5: Vikram Singh (2024EC005) - Improving
        record_attempt(student_objs[4], math_exam, 1, [0, 1], 12, 1200)             # 33.33% (Fail)
        record_attempt(student_objs[4], math_exam, 2, [0, 1, 2, 3], 5, 980)         # 66.67% (Pass)
        record_attempt(student_objs[4], python_exam, 1, [0, 2, 3], 3, 900)          # 50%

        db.session.commit()
        print("Database seeded successfully with realistic exams, questions, students, and performance logs!")

if __name__ == "__main__":
    seed_database()
