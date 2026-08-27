import os
import csv
import io
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, Response, abort
)
from config import Config
from models import db, User, Exam, Question, Option, ExamAttempt, StudentAnswer

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # -------------------------------------------------------------
    # Context Processors & Template Filters
    # -------------------------------------------------------------
    @app.context_processor
    def inject_globals():
        current_user = None
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
        return {
            'current_user': current_user,
            'now': datetime.utcnow(),
            'app_name': 'ExamSphere Pro - Examination & Performance Analysis System'
        }

    @app.template_filter('datetime_format')
    def datetime_format_filter(value, format='%d %b %Y, %I:%M %p'):
        if not value:
            return 'N/A'
        return value.strftime(format)

    @app.template_filter('date_format')
    def date_format_filter(value, format='%d %b %Y'):
        if not value:
            return 'N/A'
        return value.strftime(format)

    # -------------------------------------------------------------
    # Authentication & Authorization Decorators
    # -------------------------------------------------------------
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    def student_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            user = db.session.get(User, session['user_id'])
            if not user or user.role != 'student':
                flash('Access denied: Student account required.', 'danger')
                return redirect(url_for('admin_dashboard') if user and user.is_admin else url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in as an administrator.', 'warning')
                return redirect(url_for('login', next=request.url))
            user = db.session.get(User, session['user_id'])
            if not user or not user.is_admin:
                flash('Access denied: Administrator privileges required.', 'danger')
                return redirect(url_for('student_dashboard') if user else url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    # -------------------------------------------------------------
    # General / Auth Routes
    # -------------------------------------------------------------
    @app.route('/')
    def index():
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user:
                return redirect(url_for('admin_dashboard' if user.is_admin else 'student_dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user:
                return redirect(url_for('admin_dashboard' if user.is_admin else 'student_dashboard'))

        if request.method == 'POST':
            login_id = request.form.get('login_id', '').strip()
            password = request.form.get('password', '').strip()
            remember = request.form.get('remember') == 'on'

            if not login_id or not password:
                flash('Please provide both username/email and password.', 'warning')
                return render_template('auth/login.html')

            # Search by email or register number
            user = User.query.filter(
                (User.email.ilike(login_id)) | (User.register_no.ilike(login_id))
            ).first()

            if user and user.check_password(password):
                session.clear()
                session['user_id'] = user.id
                session['user_name'] = user.full_name
                session['user_role'] = user.role
                session.permanent = remember

                flash(f'Welcome back, {user.full_name}!', 'success')
                next_page = request.args.get('next')
                if next_page and not next_page.startswith('//') and not next_page.startswith('http'):
                    return redirect(next_page)
                return redirect(url_for('admin_dashboard' if user.is_admin else 'student_dashboard'))
            else:
                flash('Invalid credentials. Please verify your ID and password.', 'danger')

        return render_template('auth/login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('index'))

        if request.method == 'POST':
            register_no = request.form.get('register_no', '').strip().upper()
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            department = request.form.get('department', '').strip()
            semester = request.form.get('semester', type=int) or 6

            if not all([register_no, full_name, email, password, confirm_password, department]):
                flash('All fields marked with an asterisk are required.', 'warning')
                return render_template('auth/register.html')

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('auth/register.html')

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'warning')
                return render_template('auth/register.html')

            # Duplicate checks
            if User.query.filter_by(register_no=register_no).first():
                flash(f'Register Number "{register_no}" is already registered.', 'danger')
                return render_template('auth/register.html')

            if User.query.filter_by(email=email).first():
                flash(f'Email address "{email}" is already in use.', 'danger')
                return render_template('auth/register.html')

            new_student = User(
                register_no=register_no,
                full_name=full_name,
                email=email,
                role='student',
                department=department,
                semester=semester
            )
            new_student.set_password(password)
            db.session.add(new_student)
            db.session.commit()

            flash('Registration successful! You can now log in with your credentials.', 'success')
            return redirect(url_for('login'))

        return render_template('auth/register.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out safely.', 'info')
        return redirect(url_for('login'))

    # -------------------------------------------------------------
    # Student Module Routes
    # -------------------------------------------------------------
    @app.route('/student/dashboard')
    @student_required
    def student_dashboard():
        student = db.session.get(User, session['user_id'])
        
        # All available active exams
        active_exams = Exam.query.filter_by(is_active=True).all()
        
        # Student's completed attempts
        completed_attempts = ExamAttempt.query.filter_by(
            user_id=student.id, status='completed'
        ).order_by(ExamAttempt.submitted_at.desc()).all()

        # In-progress attempts (if any)
        in_progress_attempt = ExamAttempt.query.filter_by(
            user_id=student.id, status='in_progress'
        ).first()

        # Performance Summary Metrics
        total_exams_taken = len(completed_attempts)
        if total_exams_taken > 0:
            overall_avg_percentage = round(sum(a.percentage for a in completed_attempts) / total_exams_taken, 2)
            passed_count = sum(1 for a in completed_attempts if a.is_passed)
            pass_rate = round((passed_count / total_exams_taken) * 100.0, 1)
            highest_score_attempt = max(completed_attempts, key=lambda a: a.percentage)
        else:
            overall_avg_percentage = 0.0
            passed_count = 0
            pass_rate = 0.0
            highest_score_attempt = None

        # Distinct exams attempted
        distinct_exams_attempted_ids = {a.exam_id for a in completed_attempts}

        return render_template(
            'student/dashboard.html',
            student=student,
            active_exams=active_exams,
            completed_attempts=completed_attempts[:5], # Latest 5
            in_progress_attempt=in_progress_attempt,
            total_exams_taken=total_exams_taken,
            overall_avg_percentage=overall_avg_percentage,
            passed_count=passed_count,
            pass_rate=pass_rate,
            highest_score_attempt=highest_score_attempt,
            distinct_exams_count=len(distinct_exams_attempted_ids)
        )

    @app.route('/student/exams')
    @student_required
    def student_exams():
        student = db.session.get(User, session['user_id'])
        exams = Exam.query.filter_by(is_active=True).order_by(Exam.created_at.desc()).all()
        
        # Map user attempt counts per exam
        exam_stats = {}
        for ex in exams:
            user_attempts = ExamAttempt.query.filter_by(user_id=student.id, exam_id=ex.id, status='completed').order_by(ExamAttempt.submitted_at.desc()).all()
            exam_stats[ex.id] = {
                'attempts_count': len(user_attempts),
                'best_score': max([a.percentage for a in user_attempts], default=None),
                'latest_attempt': user_attempts[0] if user_attempts else None
            }

        return render_template('student/exams.html', exams=exams, exam_stats=exam_stats)

    @app.route('/student/exam/<int:exam_id>/instructions')
    @student_required
    def exam_instructions(exam_id):
        exam = db.session.get(Exam, exam_id)
        if not exam or not exam.is_active:
            flash('The requested exam is currently unavailable.', 'danger')
            return redirect(url_for('student_exams'))

        student = db.session.get(User, session['user_id'])
        previous_attempts = ExamAttempt.query.filter_by(user_id=student.id, exam_id=exam.id, status='completed').all()

        return render_template('student/instructions.html', exam=exam, previous_attempts=previous_attempts)

    @app.route('/student/exam/<int:exam_id>/start', methods=['POST'])
    @student_required
    def start_exam(exam_id):
        exam = db.session.get(Exam, exam_id)
        if not exam or not exam.is_active:
            flash('The requested exam is not available.', 'danger')
            return redirect(url_for('student_exams'))

        if exam.total_questions == 0:
            flash('This exam does not have any questions yet. Please contact the administrator.', 'warning')
            return redirect(url_for('student_exams'))

        student = db.session.get(User, session['user_id'])

        # Check if there is already an in-progress attempt for this exam
        existing_attempt = ExamAttempt.query.filter_by(
            user_id=student.id, exam_id=exam.id, status='in_progress'
        ).first()

        if existing_attempt:
            # Check if time expired
            elapsed = (datetime.utcnow() - existing_attempt.start_time).total_seconds()
            allocated = exam.duration_minutes * 60
            if elapsed > allocated + 30: # 30s grace period
                existing_attempt.status = 'timed_out'
                existing_attempt.submitted_at = existing_attempt.start_time + timedelta(minutes=exam.duration_minutes)
                db.session.commit()
            else:
                return redirect(url_for('take_exam', attempt_id=existing_attempt.id))

        # Count prior attempts to set attempt_number
        prior_count = ExamAttempt.query.filter_by(user_id=student.id, exam_id=exam.id).count()

        new_attempt = ExamAttempt(
            user_id=student.id,
            exam_id=exam.id,
            attempt_number=prior_count + 1,
            start_time=datetime.utcnow(),
            status='in_progress'
        )
        db.session.add(new_attempt)
        db.session.commit()

        return redirect(url_for('take_exam', attempt_id=new_attempt.id))

    @app.route('/student/attempt/<int:attempt_id>/take')
    @student_required
    def take_exam(attempt_id):
        attempt = db.session.get(ExamAttempt, attempt_id)
        if not attempt or attempt.user_id != session['user_id']:
            flash('Exam attempt not found.', 'danger')
            return redirect(url_for('student_dashboard'))

        if attempt.status != 'in_progress':
            flash('This exam attempt has already been submitted.', 'info')
            return redirect(url_for('exam_result', attempt_id=attempt.id))

        exam = attempt.exam
        # Calculate time remaining
        elapsed_seconds = int((datetime.utcnow() - attempt.start_time).total_seconds())
        total_allowed_seconds = exam.duration_minutes * 60
        remaining_seconds = max(0, total_allowed_seconds - elapsed_seconds)

        if remaining_seconds <= 0:
            # Auto-submit empty if timed out
            attempt.status = 'timed_out'
            attempt.submitted_at = attempt.start_time + timedelta(minutes=exam.duration_minutes)
            attempt.time_taken_seconds = total_allowed_seconds
            attempt.total_score = 0.0
            attempt.max_score = exam.total_marks
            attempt.percentage = 0.0
            db.session.commit()
            flash('Your time limit has expired. The exam was auto-submitted.', 'warning')
            return redirect(url_for('exam_result', attempt_id=attempt.id))

        questions = exam.questions
        return render_template(
            'student/take_exam.html',
            attempt=attempt,
            exam=exam,
            questions=questions,
            remaining_seconds=remaining_seconds,
            total_allowed_seconds=total_allowed_seconds
        )

    @app.route('/student/attempt/<int:attempt_id>/submit', methods=['POST'])
    @student_required
    def submit_exam(attempt_id):
        attempt = db.session.get(ExamAttempt, attempt_id)
        if not attempt or attempt.user_id != session['user_id']:
            flash('Invalid exam attempt.', 'danger')
            return redirect(url_for('student_dashboard'))

        if attempt.status != 'in_progress':
            flash('This attempt has already been evaluated.', 'info')
            return redirect(url_for('exam_result', attempt_id=attempt.id))

        exam = attempt.exam
        submission_time = datetime.utcnow()
        elapsed_seconds = int((submission_time - attempt.start_time).total_seconds())
        allowed_seconds = (exam.duration_minutes * 60) + 60 # 60s network latency tolerance

        total_score = 0.0
        max_possible_marks = 0.0

        # Remove any lingering partial answers for this attempt
        StudentAnswer.query.filter_by(attempt_id=attempt.id).delete()

        for question in exam.questions:
            max_possible_marks += question.marks
            selected_option_id = request.form.get(f'question_{question.id}', type=int)

            is_correct = False
            marks_awarded = 0.0

            if selected_option_id:
                option = db.session.get(Option, selected_option_id)
                if option and option.question_id == question.id and option.is_correct:
                    is_correct = True
                    marks_awarded = question.marks
                    total_score += marks_awarded

            answer = StudentAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=selected_option_id,
                is_correct=is_correct,
                marks_awarded=marks_awarded
            )
            db.session.add(answer)

        # Update attempt fields
        attempt.submitted_at = submission_time
        attempt.time_taken_seconds = min(elapsed_seconds, exam.duration_minutes * 60)
        attempt.total_score = round(total_score, 2)
        attempt.max_score = round(max_possible_marks, 2)
        attempt.percentage = round((total_score / max_possible_marks) * 100.0, 2) if max_possible_marks > 0 else 0.0
        attempt.status = 'completed'

        db.session.commit()
        flash('Exam submitted successfully! Review your detailed score card below.', 'success')
        return redirect(url_for('exam_result', attempt_id=attempt.id))

    @app.route('/student/attempt/<int:attempt_id>/result')
    @login_required
    def exam_result(attempt_id):
        attempt = db.session.get(ExamAttempt, attempt_id)
        if not attempt:
            flash('Attempt not found.', 'danger')
            return redirect(url_for('index'))

        current_user = db.session.get(User, session['user_id'])
        # Allow only the owner or an admin
        if not current_user.is_admin and attempt.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('student_dashboard'))

        # Fetch answers and questions
        answers = StudentAnswer.query.filter_by(attempt_id=attempt.id).all()
        answers_map = {ans.question_id: ans for ans in answers}

        correct_count = sum(1 for a in answers if a.is_correct)
        unanswered_count = sum(1 for a in answers if a.selected_option_id is None)
        incorrect_count = len(answers) - correct_count - unanswered_count

        return render_template(
            'student/result.html',
            attempt=attempt,
            exam=attempt.exam,
            student=attempt.user,
            answers_map=answers_map,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unanswered_count=unanswered_count
        )

    # -------------------------------------------------------------
    # Performance Analysis & Report Card Module
    # -------------------------------------------------------------
    def compute_student_performance(student_id):
        """Helper to compute deep metrics, attempt progressions, subject summaries, and chart data."""
        student = db.session.get(User, student_id)
        if not student:
            return None

        attempts = ExamAttempt.query.filter_by(
            user_id=student.id, status='completed'
        ).order_by(ExamAttempt.submitted_at.asc()).all()

        total_attempts = len(attempts)
        if total_attempts == 0:
            return {
                'student': student,
                'total_attempts': 0,
                'overall_average': 0.0,
                'highest_percentage': 0.0,
                'pass_rate': 0.0,
                'subject_summaries': [],
                'comparison_list': [],
                'chart_data': {
                    'subject_labels': [],
                    'subject_latest_scores': [],
                    'subject_best_scores': [],
                    'timeline_labels': [],
                    'timeline_scores': [],
                    'accuracy_counts': [0, 0, 0]
                }
            }

        overall_average = round(sum(a.percentage for a in attempts) / total_attempts, 2)
        highest_percentage = round(max(a.percentage for a in attempts), 2)
        passed_attempts = sum(1 for a in attempts if a.is_passed)
        pass_rate = round((passed_attempts / total_attempts) * 100.0, 1)

        # Subject-wise groupings
        exams_dict = {}
        for att in attempts:
            if att.exam_id not in exams_dict:
                exams_dict[att.exam_id] = []
            exams_dict[att.exam_id].append(att)

        subject_summaries = []
        comparison_list = []

        total_correct_ans = 0
        total_incorrect_ans = 0
        total_unanswered_ans = 0

        for exam_id, att_list in exams_dict.items():
            exam = db.session.get(Exam, exam_id)
            if not exam:
                continue

            att_list_sorted = sorted(att_list, key=lambda x: x.attempt_number)
            first_attempt = att_list_sorted[0]
            latest_attempt = att_list_sorted[-1]
            best_score = max(a.percentage for a in att_list_sorted)
            avg_score = round(sum(a.percentage for a in att_list_sorted) / len(att_list_sorted), 2)

            subject_summaries.append({
                'exam': exam,
                'attempts_count': len(att_list_sorted),
                'first_score': first_attempt.percentage,
                'latest_score': latest_attempt.percentage,
                'best_score': best_score,
                'average_score': avg_score,
                'latest_grade': latest_attempt.grade,
                'is_passed': latest_attempt.is_passed,
                'latest_date': latest_attempt.submitted_at
            })

            # Previous vs Current comparison
            if len(att_list_sorted) > 1:
                prev_attempt = att_list_sorted[-2]
                curr_attempt = att_list_sorted[-1]
                delta = round(curr_attempt.percentage - prev_attempt.percentage, 2)
                comparison_list.append({
                    'exam': exam,
                    'previous_attempt_no': prev_attempt.attempt_number,
                    'previous_score': prev_attempt.percentage,
                    'previous_date': prev_attempt.submitted_at,
                    'current_attempt_no': curr_attempt.attempt_number,
                    'current_score': curr_attempt.percentage,
                    'current_date': curr_attempt.submitted_at,
                    'delta': delta,
                    'trend': 'up' if delta > 0 else ('down' if delta < 0 else 'neutral')
                })
            else:
                # Only 1 attempt
                comparison_list.append({
                    'exam': exam,
                    'previous_attempt_no': '-',
                    'previous_score': None,
                    'previous_date': None,
                    'current_attempt_no': 1,
                    'current_score': latest_attempt.percentage,
                    'current_date': latest_attempt.submitted_at,
                    'delta': 0.0,
                    'trend': 'first'
                })

            # Calculate accuracy counts from all answers
            for att in att_list:
                for ans in att.answers:
                    if ans.is_correct:
                        total_correct_ans += 1
                    elif ans.selected_option_id is None:
                        total_unanswered_ans += 1
                    else:
                        total_incorrect_ans += 1

        # Chart Data Preparations
        subject_labels = [s['exam'].course_code for s in subject_summaries]
        subject_latest_scores = [s['latest_score'] for s in subject_summaries]
        subject_best_scores = [s['best_score'] for s in subject_summaries]

        timeline_labels = [f"{a.exam.course_code} (Att #{a.attempt_number})" for a in attempts]
        timeline_scores = [a.percentage for a in attempts]

        return {
            'student': student,
            'total_attempts': total_attempts,
            'overall_average': overall_average,
            'highest_percentage': highest_percentage,
            'pass_rate': pass_rate,
            'subject_summaries': subject_summaries,
            'comparison_list': comparison_list,
            'chart_data': {
                'subject_labels': subject_labels,
                'subject_latest_scores': subject_latest_scores,
                'subject_best_scores': subject_best_scores,
                'timeline_labels': timeline_labels,
                'timeline_scores': timeline_scores,
                'accuracy_counts': [total_correct_ans, total_incorrect_ans, total_unanswered_ans]
            }
        }

    @app.route('/student/performance')
    @student_required
    def student_performance():
        student = db.session.get(User, session['user_id'])
        perf_data = compute_student_performance(student.id)
        return render_template('student/performance.html', **perf_data)

    @app.route('/student/report-card')
    @student_required
    def student_report_card():
        student = db.session.get(User, session['user_id'])
        perf_data = compute_student_performance(student.id)
        return render_template('student/report_card.html', **perf_data)

    # -------------------------------------------------------------
    # Admin Module Routes
    # -------------------------------------------------------------
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        total_students = User.query.filter_by(role='student').count()
        total_exams = Exam.query.count()
        total_questions = Question.query.count()
        total_attempts = ExamAttempt.query.filter_by(status='completed').count()

        all_completed = ExamAttempt.query.filter_by(status='completed').all()
        if all_completed:
            global_avg = round(sum(a.percentage for a in all_completed) / len(all_completed), 2)
            passed_count = sum(1 for a in all_completed if a.is_passed)
            global_pass_rate = round((passed_count / len(all_completed)) * 100.0, 1)
        else:
            global_avg = 0.0
            global_pass_rate = 0.0

        recent_attempts = ExamAttempt.query.filter_by(status='completed').order_by(ExamAttempt.submitted_at.desc()).limit(8).all()

        # Exam analytics for chart
        exams = Exam.query.all()
        exam_names = []
        exam_averages = []
        exam_attempt_counts = []

        for ex in exams:
            ex_attempts = [a for a in all_completed if a.exam_id == ex.id]
            exam_names.append(ex.course_code)
            exam_attempt_counts.append(len(ex_attempts))
            if ex_attempts:
                exam_averages.append(round(sum(a.percentage for a in ex_attempts) / len(ex_attempts), 2))
            else:
                exam_averages.append(0.0)

        # Grade distribution
        grades_dist = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'P': 0, 'F': 0}
        for a in all_completed:
            g = a.grade
            if g in grades_dist:
                grades_dist[g] += 1

        return render_template(
            'admin/dashboard.html',
            total_students=total_students,
            total_exams=total_exams,
            total_questions=total_questions,
            total_attempts=total_attempts,
            global_avg=global_avg,
            global_pass_rate=global_pass_rate,
            recent_attempts=recent_attempts,
            exam_names=exam_names,
            exam_averages=exam_averages,
            exam_attempt_counts=exam_attempt_counts,
            grades_labels=list(grades_dist.keys()),
            grades_values=list(grades_dist.values())
        )

    @app.route('/admin/exams')
    @admin_required
    def admin_exams():
        exams = Exam.query.order_by(Exam.created_at.desc()).all()
        return render_template('admin/exams.html', exams=exams)

    @app.route('/admin/exams/create', methods=['GET', 'POST'])
    @admin_required
    def create_exam():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            course_code = request.form.get('course_code', '').strip().upper()
            description = request.form.get('description', '').strip()
            duration_minutes = request.form.get('duration_minutes', type=int) or 30
            pass_percentage = request.form.get('pass_percentage', type=float) or 40.0
            is_active = request.form.get('is_active') == 'on'

            if not title or not course_code:
                flash('Exam Title and Course Code are required.', 'warning')
                return render_template('admin/exam_form.html', action='Create', exam=None)

            new_exam = Exam(
                title=title,
                course_code=course_code,
                description=description,
                duration_minutes=duration_minutes,
                pass_percentage=pass_percentage,
                is_active=is_active,
                created_by=session['user_id']
            )
            db.session.add(new_exam)
            db.session.commit()

            flash(f'Exam "{course_code}: {title}" created successfully! Now add questions to it.', 'success')
            return redirect(url_for('admin_exam_questions', exam_id=new_exam.id))

        return render_template('admin/exam_form.html', action='Create', exam=None)

    @app.route('/admin/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def edit_exam(exam_id):
        exam = db.session.get(Exam, exam_id)
        if not exam:
            flash('Exam not found.', 'danger')
            return redirect(url_for('admin_exams'))

        if request.method == 'POST':
            exam.title = request.form.get('title', '').strip()
            exam.course_code = request.form.get('course_code', '').strip().upper()
            exam.description = request.form.get('description', '').strip()
            exam.duration_minutes = request.form.get('duration_minutes', type=int) or 30
            exam.pass_percentage = request.form.get('pass_percentage', type=float) or 40.0
            exam.is_active = request.form.get('is_active') == 'on'

            if not exam.title or not exam.course_code:
                flash('Exam Title and Course Code are required.', 'warning')
                return render_template('admin/exam_form.html', action='Edit', exam=exam)

            db.session.commit()
            flash('Exam details updated successfully.', 'success')
            return redirect(url_for('admin_exams'))

        return render_template('admin/exam_form.html', action='Edit', exam=exam)

    @app.route('/admin/exams/<int:exam_id>/toggle-status', methods=['POST'])
    @admin_required
    def toggle_exam_status(exam_id):
        exam = db.session.get(Exam, exam_id)
        if not exam:
            flash('Exam not found.', 'danger')
            return redirect(url_for('admin_exams'))

        exam.is_active = not exam.is_active
        db.session.commit()
        status_str = 'Activated' if exam.is_active else 'Deactivated'
        flash(f'Exam "{exam.course_code}" has been {status_str}.', 'info')
        return redirect(url_for('admin_exams'))

    @app.route('/admin/exams/<int:exam_id>/delete', methods=['POST'])
    @admin_required
    def delete_exam(exam_id):
        exam = db.session.get(Exam, exam_id)
        if not exam:
            flash('Exam not found.', 'danger')
            return redirect(url_for('admin_exams'))

        title = exam.title
        db.session.delete(exam)
        db.session.commit()
        flash(f'Exam "{title}" and all associated questions & attempts have been deleted.', 'success')
        return redirect(url_for('admin_exams'))

    # Question Management
    @app.route('/admin/exams/<int:exam_id>/questions')
    @admin_required
    def admin_exam_questions(exam_id):
        exam = db.session.get(Exam, exam_id)
        if not exam:
            flash('Exam not found.', 'danger')
            return redirect(url_for('admin_exams'))

        questions = Question.query.filter_by(exam_id=exam.id).order_by(Question.id.asc()).all()
        return render_template('admin/questions.html', exam=exam, questions=questions)

    @app.route('/admin/exams/<int:exam_id>/questions/create', methods=['GET', 'POST'])
    @admin_required
    def create_question(exam_id):
        exam = db.session.get(Exam, exam_id)
        if not exam:
            flash('Exam not found.', 'danger')
            return redirect(url_for('admin_exams'))

        if request.method == 'POST':
            question_text = request.form.get('question_text', '').strip()
            marks = request.form.get('marks', type=float) or 1.0
            explanation = request.form.get('explanation', '').strip()
            correct_label = request.form.get('correct_option', 'A')

            option_a = request.form.get('option_A', '').strip()
            option_b = request.form.get('option_B', '').strip()
            option_c = request.form.get('option_C', '').strip()
            option_d = request.form.get('option_D', '').strip()

            if not question_text or not all([option_a, option_b, option_c, option_d]):
                flash('Question text and all 4 options (A, B, C, D) are required.', 'warning')
                return render_template('admin/question_form.html', action='Create', exam=exam, question=None)

            new_q = Question(
                exam_id=exam.id,
                question_text=question_text,
                marks=marks,
                explanation=explanation
            )
            db.session.add(new_q)
            db.session.flush()

            options_data = [
                ('A', option_a, correct_label == 'A'),
                ('B', option_b, correct_label == 'B'),
                ('C', option_c, correct_label == 'C'),
                ('D', option_d, correct_label == 'D'),
            ]

            for lbl, txt, is_corr in options_data:
                opt = Option(
                    question_id=new_q.id,
                    option_label=lbl,
                    option_text=txt,
                    is_correct=is_corr
                )
                db.session.add(opt)

            db.session.commit()
            flash('Question added to exam successfully!', 'success')
            return redirect(url_for('admin_exam_questions', exam_id=exam.id))

        return render_template('admin/question_form.html', action='Create', exam=exam, question=None)

    @app.route('/admin/questions/<int:question_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def edit_question(question_id):
        question = db.session.get(Question, question_id)
        if not question:
            flash('Question not found.', 'danger')
            return redirect(url_for('admin_exams'))

        exam = question.exam

        if request.method == 'POST':
            question.question_text = request.form.get('question_text', '').strip()
            question.marks = request.form.get('marks', type=float) or 1.0
            question.explanation = request.form.get('explanation', '').strip()
            correct_label = request.form.get('correct_option', 'A')

            option_a = request.form.get('option_A', '').strip()
            option_b = request.form.get('option_B', '').strip()
            option_c = request.form.get('option_C', '').strip()
            option_d = request.form.get('option_D', '').strip()

            if not question.question_text or not all([option_a, option_b, option_c, option_d]):
                flash('Question text and all 4 options are required.', 'warning')
                return render_template('admin/question_form.html', action='Edit', exam=exam, question=question)

            # Update existing options
            opts_map = {opt.option_label: opt for opt in question.options}
            raw_opts = {'A': option_a, 'B': option_b, 'C': option_c, 'D': option_d}

            for lbl, txt in raw_opts.items():
                if lbl in opts_map:
                    opts_map[lbl].option_text = txt
                    opts_map[lbl].is_correct = (lbl == correct_label)
                else:
                    new_opt = Option(
                        question_id=question.id,
                        option_label=lbl,
                        option_text=txt,
                        is_correct=(lbl == correct_label)
                    )
                    db.session.add(new_opt)

            db.session.commit()
            flash('Question updated successfully.', 'success')
            return redirect(url_for('admin_exam_questions', exam_id=exam.id))

        return render_template('admin/question_form.html', action='Edit', exam=exam, question=question)

    @app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
    @admin_required
    def delete_question(question_id):
        question = db.session.get(Question, question_id)
        if not question:
            flash('Question not found.', 'danger')
            return redirect(url_for('admin_exams'))

        exam_id = question.exam_id
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully.', 'success')
        return redirect(url_for('admin_exam_questions', exam_id=exam_id))

    # Student & Results Directory
    @app.route('/admin/students')
    @admin_required
    def admin_students():
        search_query = request.args.get('q', '').strip()
        dept_filter = request.args.get('dept', '').strip()

        query = User.query.filter_by(role='student')

        if search_query:
            query = query.filter(
                (User.full_name.ilike(f"%{search_query}%")) |
                (User.register_no.ilike(f"%{search_query}%")) |
                (User.email.ilike(f"%{search_query}%"))
            )

        if dept_filter:
            query = query.filter(User.department == dept_filter)

        students = query.order_by(User.register_no.asc()).all()

        # Compute stats per student
        students_data = []
        departments = [d[0] for d in db.session.query(User.department).filter_by(role='student').distinct()]

        for s in students:
            attempts = ExamAttempt.query.filter_by(user_id=s.id, status='completed').all()
            avg_score = round(sum(a.percentage for a in attempts) / len(attempts), 2) if attempts else 0.0
            students_data.append({
                'user': s,
                'total_attempts': len(attempts),
                'average_score': avg_score,
                'last_attempt': max([a.submitted_at for a in attempts], default=None)
            })

        return render_template(
            'admin/students.html',
            students_data=students_data,
            departments=departments,
            search_query=search_query,
            selected_dept=dept_filter
        )

    @app.route('/admin/student/<int:student_id>')
    @admin_required
    def admin_student_detail(student_id):
        perf_data = compute_student_performance(student_id)
        if not perf_data:
            flash('Student not found.', 'danger')
            return redirect(url_for('admin_students'))

        return render_template('admin/student_detail.html', **perf_data)

    @app.route('/admin/student/<int:student_id>/report-card')
    @admin_required
    def admin_student_report_card(student_id):
        perf_data = compute_student_performance(student_id)
        if not perf_data:
            flash('Student not found.', 'danger')
            return redirect(url_for('admin_students'))

        return render_template('student/report_card.html', **perf_data)

    @app.route('/admin/results')
    @admin_required
    def admin_results():
        exam_id = request.args.get('exam_id', type=int)
        status = request.args.get('status', '').strip()

        query = ExamAttempt.query.join(ExamAttempt.user).join(ExamAttempt.exam)

        if exam_id:
            query = query.filter(ExamAttempt.exam_id == exam_id)
        if status:
            query = query.filter(ExamAttempt.status == status)

        attempts = query.order_by(ExamAttempt.submitted_at.desc()).all()
        exams = Exam.query.all()

        return render_template(
            'admin/all_results.html',
            attempts=attempts,
            exams=exams,
            selected_exam_id=exam_id,
            selected_status=status
        )

    @app.route('/admin/results/export-csv')
    @admin_required
    def export_results_csv():
        attempts = ExamAttempt.query.join(ExamAttempt.user).join(ExamAttempt.exam).order_by(ExamAttempt.submitted_at.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Attempt ID', 'Register Number', 'Student Name', 'Department',
            'Course Code', 'Exam Title', 'Attempt Number', 'Marks Obtained',
            'Max Marks', 'Percentage', 'Grade', 'Result Status', 'Date Submitted'
        ])

        for a in attempts:
            writer.writerow([
                a.id,
                a.user.register_no or 'N/A',
                a.user.full_name,
                a.user.department,
                a.exam.course_code,
                a.exam.title,
                a.attempt_number,
                a.total_score,
                a.max_score,
                f"{a.percentage}%",
                a.grade,
                'PASS' if a.is_passed else 'FAIL',
                a.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if a.submitted_at else 'In Progress'
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=exam_results_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'}
        )

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
