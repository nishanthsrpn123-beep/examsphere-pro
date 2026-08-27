from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    register_no = db.Column(db.String(50), unique=True, index=True, nullable=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student', nullable=False)  # 'student' or 'admin'
    department = db.Column(db.String(120), default='Computer Science & Engineering')
    semester = db.Column(db.Integer, default=6)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    attempts = db.relationship('ExamAttempt', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    created_exams = db.relationship('Exam', back_populates='creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.register_no or self.email} ({self.role})>"


class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    course_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, default=30, nullable=False)
    pass_percentage = db.Column(db.Float, default=40.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship('User', back_populates='created_exams')
    questions = db.relationship('Question', back_populates='exam', cascade='all, delete-orphan', order_by='Question.id')
    attempts = db.relationship('ExamAttempt', back_populates='exam', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def total_questions(self):
        return len(self.questions)

    @property
    def total_marks(self):
        return sum(q.marks for q in self.questions)

    def __repr__(self):
        return f"<Exam {self.course_code}: {self.title}>"


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Float, default=1.0, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    exam = db.relationship('Exam', back_populates='questions')
    options = db.relationship('Option', back_populates='question', cascade='all, delete-orphan', order_by='Option.id')

    @property
    def correct_option(self):
        for opt in self.options:
            if opt.is_correct:
                return opt
        return None

    def __repr__(self):
        return f"<Question {self.id} (Exam {self.exam_id})>"


class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    option_label = db.Column(db.String(10), nullable=False)  # 'A', 'B', 'C', 'D'
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    question = db.relationship('Question', back_populates='options')

    def __repr__(self):
        return f"<Option {self.option_label}: {self.option_text[:20]}>"


class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    attempt_number = db.Column(db.Integer, default=1, nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    time_taken_seconds = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Float, default=0.0)
    max_score = db.Column(db.Float, default=0.0)
    percentage = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='in_progress', nullable=False)  # 'in_progress', 'completed', 'timed_out'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='attempts')
    exam = db.relationship('Exam', back_populates='attempts')
    answers = db.relationship('StudentAnswer', back_populates='attempt', cascade='all, delete-orphan', order_by='StudentAnswer.id')

    @property
    def is_passed(self):
        if not self.exam:
            return self.percentage >= 40.0
        return self.percentage >= self.exam.pass_percentage

    @property
    def grade(self):
        if self.percentage >= 90:
            return 'A+'
        elif self.percentage >= 80:
            return 'A'
        elif self.percentage >= 70:
            return 'B+'
        elif self.percentage >= 60:
            return 'B'
        elif self.percentage >= 50:
            return 'C'
        elif self.percentage >= 40:
            return 'P'
        else:
            return 'F'

    @property
    def formatted_time_taken(self):
        mins = self.time_taken_seconds // 60
        secs = self.time_taken_seconds % 60
        return f"{mins}m {secs}s"

    def __repr__(self):
        return f"<ExamAttempt {self.id} User:{self.user_id} Exam:{self.exam_id} Score:{self.total_score}/{self.max_score}>"


class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempts.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='SET NULL'), nullable=True)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    marks_awarded = db.Column(db.Float, default=0.0, nullable=False)

    # Relationships
    attempt = db.relationship('ExamAttempt', back_populates='answers')
    question = db.relationship('Question')
    selected_option = db.relationship('Option')

    def __repr__(self):
        return f"<StudentAnswer Attempt:{self.attempt_id} Question:{self.question_id} Correct:{self.is_correct}>"
