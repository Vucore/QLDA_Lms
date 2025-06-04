from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import app, db
from models import User, Student, Instructor, Course, Lesson, Assignment, Submission, Grade, Schedule
from forms import (LoginForm, RegistrationForm, CourseForm, LessonForm, AssignmentForm, 
                  SubmissionForm, GradeForm, ScheduleForm, UserForm)
from utils import role_required
import logging

# Home page
@app.route('/')
def index():
    featured_courses = Course.query.limit(3).all()
    return render_template('index.html', featured_courses=featured_courses)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='student'  # Default role is student, can be changed by admin later
        )
        user.set_password(form.password.data)
        
        # Create student profile for all new users
        profile = Student(
            user=user,
            full_name=form.full_name.data
        )
        
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserForm()
    
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.role.data = current_user.role
        
        if current_user.is_student():
            form.full_name.data = current_user.student_profile.full_name
        elif current_user.is_instructor():
            form.full_name.data = current_user.instructor_profile.full_name
            form.expertise.data = current_user.instructor_profile.expertise
    
    if form.validate_on_submit():
        # Update user data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Update profile data
        if current_user.is_student():
            current_user.student_profile.full_name = form.full_name.data
        elif current_user.is_instructor():
            current_user.instructor_profile.full_name = form.full_name.data
            current_user.instructor_profile.expertise = form.expertise.data
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/profile.html', form=form)

# Dashboard routes
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_instructor():
        return redirect(url_for('instructor_dashboard'))
    else:  # student
        return redirect(url_for('student_dashboard'))

@app.route('/dashboard/student')
@login_required
@role_required('student')
def student_dashboard():
    # Get student profile
    student = current_user.student_profile
    
    # Get enrolled courses
    enrolled_courses = student.enrolled_courses
    
    # Get upcoming assignments
    upcoming_assignments = []
    for course in enrolled_courses:
        assignments = Assignment.query.filter_by(course_id=course.id).filter(Assignment.deadline >= datetime.utcnow()).order_by(Assignment.deadline).all()
        upcoming_assignments.extend(assignments)
    
    # Get recent submissions
    recent_submissions = Submission.query.filter_by(student_id=student.id).order_by(Submission.submitted_at.desc()).limit(5).all()
    
    # Get upcoming schedules
    upcoming_schedules = []
    for course in enrolled_courses:
        schedules = Schedule.query.filter_by(course_id=course.id).filter(Schedule.date >= datetime.utcnow().date()).order_by(Schedule.date, Schedule.start_time).all()
        upcoming_schedules.extend(schedules)
    
    return render_template('dashboard/student.html', 
                           student=student, 
                           enrolled_courses=enrolled_courses, 
                           upcoming_assignments=upcoming_assignments,
                           recent_submissions=recent_submissions,
                           upcoming_schedules=upcoming_schedules)

@app.route('/student/courses')
@login_required
@role_required('student')
def student_courses():
    # Get student profile
    student = current_user.student_profile
    
    # Get enrolled courses
    enrolled_courses = student.enrolled_courses
    
    # Get recommended courses (courses not enrolled in)
    recommended_courses = Course.query.filter(~Course.id.in_([c.id for c in enrolled_courses])).limit(3).all()
    
    return render_template('courses/student_courses.html',
                          student=student,
                          enrolled_courses=enrolled_courses,
                          recommended_courses=recommended_courses)

@app.route('/dashboard/instructor')
@login_required
@role_required('instructor')
def instructor_dashboard():
    # Get instructor profile
    instructor = current_user.instructor_profile
    
    # Get instructor's courses
    courses = instructor.courses.all()
    
    # Get recent assignments
    recent_assignments = []
    for course in courses:
        assignments = Assignment.query.filter_by(course_id=course.id).order_by(Assignment.created_at.desc()).limit(3).all()
        recent_assignments.extend(assignments)
    
    # Get recent submissions needing grading
    submissions_needing_grading = []
    for course in courses:
        for assignment in course.assignments:
            submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
            for submission in submissions:
                if not submission.grade:  # No grade yet
                    submissions_needing_grading.append(submission)
    
    # Get upcoming schedules
    upcoming_schedules = []
    for course in courses:
        schedules = Schedule.query.filter_by(course_id=course.id).filter(Schedule.date >= datetime.utcnow().date()).order_by(Schedule.date, Schedule.start_time).all()
        upcoming_schedules.extend(schedules)
    
    return render_template('dashboard/instructor.html', 
                           instructor=instructor, 
                           courses=courses, 
                           recent_assignments=recent_assignments,
                           submissions_needing_grading=submissions_needing_grading,
                           upcoming_schedules=upcoming_schedules)

@app.route('/instructor/courses')
@login_required
@role_required('instructor')
def instructor_courses():
    # Get instructor profile
    instructor = current_user.instructor_profile
    
    # Get instructor's courses
    courses = instructor.courses.all()
    
    return render_template('courses/instructor_courses.html',
                          instructor=instructor,
                          courses=courses)

@app.route('/dashboard/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    # Get counts for dashboard
    user_count = User.query.count()
    student_count = Student.query.count()
    instructor_count = Instructor.query.count()
    course_count = Course.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get all courses
    courses = Course.query.all()
    
    return render_template('dashboard/admin.html', 
                           user_count=user_count,
                           student_count=student_count,
                           instructor_count=instructor_count,
                           course_count=course_count,
                           recent_users=recent_users,
                           courses=courses)

# Course routes
@app.route('/courses')
def courses():
    courses = Course.query.all()
    return render_template('courses/index.html', courses=courses)

@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = course.lessons.order_by(Lesson.order).all()
    assignments = course.assignments.all()
    schedules = course.schedules.filter(Schedule.date >= datetime.utcnow().date()).order_by(Schedule.date, Schedule.start_time).all()
    
    # Check if current user is enrolled
    is_enrolled = False
    if current_user.is_authenticated and current_user.is_student():
        is_enrolled = course in current_user.student_profile.enrolled_courses
    
    return render_template('courses/detail.html', 
                           course=course, 
                           lessons=lessons, 
                           assignments=assignments,
                           schedules=schedules,
                           is_enrolled=is_enrolled,
                           Course=Course)

@app.route('/courses/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def course_create():
    form = CourseForm()
    
    # Get all instructors for the selection dropdown
    instructors = Instructor.query.all()
    
    if form.validate_on_submit():
        try:
            # Get the selected instructor
            instructor_id = request.form.get('instructor_id')
            if not instructor_id:
                flash('Please select an instructor for this course.', 'danger')
                return render_template('courses/create.html', form=form, instructors=instructors)
            
            instructor = Instructor.query.get(instructor_id)
            if not instructor:
                flash('Selected instructor not found.', 'danger')
                return render_template('courses/create.html', form=form, instructors=instructors)
            
            # Create the course
            course = Course(
                name=form.name.data,
                description=form.description.data,
                image_url=form.image_url.data or None,
                instructor=instructor
            )
            
            db.session.add(course)
            db.session.commit()
            
            # Process schedule items
            schedule_days = request.form.getlist('schedule_day[]')
            schedule_start_times = request.form.getlist('schedule_start_time[]')
            schedule_end_times = request.form.getlist('schedule_end_time[]')
            schedule_locations = request.form.getlist('schedule_location[]')
            
            # Create schedule entries
            for i in range(len(schedule_days)):
                if schedule_days[i] and schedule_start_times[i] and schedule_end_times[i]:
                    # Convert day name to next occurrence of that day
                    day_name = schedule_days[i]
                    today = datetime.now().date()
                    day_idx = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
                              'Friday': 4, 'Saturday': 5, 'Sunday': 6}
                    
                    # Calculate days until next occurrence
                    days_ahead = day_idx[day_name] - today.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    
                    next_day = today + timedelta(days=days_ahead)
                    
                    # Create time objects
                    start_time = datetime.strptime(schedule_start_times[i], '%H:%M').time()
                    end_time = datetime.strptime(schedule_end_times[i], '%H:%M').time()
                    
                    # Create the schedule
                    schedule = Schedule(
                        date=next_day,
                        start_time=start_time,
                        end_time=end_time,
                        topic=f"Weekly {day_name} class",
                        course_id=course.id,
                        location=schedule_locations[i] if schedule_locations[i] else "Online"
                    )
                    
                    db.session.add(schedule)
            
            db.session.commit()
            
            flash('Course created successfully with weekly schedule!', 'success')
            return redirect(url_for('course_detail', course_id=course.id))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating course: {str(e)}")
            flash(f'Error creating course: {str(e)}', 'danger')
    
    return render_template('courses/create.html', form=form, instructors=instructors, Course=Course)

@app.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def course_edit(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You do not have permission to edit this course.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    if current_user.role == 'student':
        flash('Students cannot edit courses.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    form = CourseForm()
    
    if request.method == 'GET':
        form.name.data = course.name
        form.description.data = course.description
        form.image_url.data = course.image_url
    
    if form.validate_on_submit():
        course.name = form.name.data
        course.description = form.description.data
        course.image_url = form.image_url.data or None
        
        db.session.commit()
        
        flash('Course updated successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
    
    return render_template('courses/edit.html', form=form, course=course)

@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
@role_required('student')
def course_enroll(course_id):
    course = Course.query.get_or_404(course_id)
    student = current_user.student_profile
    
    if course in student.enrolled_courses:
        flash('You are already enrolled in this course.', 'info')
    else:
        student.enrolled_courses.append(course)
        db.session.commit()
        flash('Enrolled in course successfully!', 'success')
    
    return redirect(url_for('course_detail', course_id=course.id))

@app.route('/courses/<int:course_id>/unenroll', methods=['POST'])
@login_required
@role_required('student')
def course_unenroll(course_id):
    course = Course.query.get_or_404(course_id)
    student = current_user.student_profile
    
    if course in student.enrolled_courses:
        student.enrolled_courses.remove(course)
        db.session.commit()
        flash('Unenrolled from course successfully!', 'info')
    else:
        flash('You are not enrolled in this course.', 'warning')
    
    return redirect(url_for('course_detail', course_id=course.id))

@app.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def course_delete(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You do not have permission to delete this course.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    if current_user.role == 'student':
        flash('Students cannot delete courses.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    # Delete the course
    db.session.delete(course)
    db.session.commit()
    
    flash('Course deleted successfully!', 'success')
    
    # Redirect based on user role
    if current_user.role == 'instructor':
        return redirect(url_for('instructor_courses'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin_courses'))
    else:
        return redirect(url_for('courses'))

# Lesson routes
@app.route('/courses/<int:course_id>/lessons/create', methods=['GET', 'POST'])
@login_required
def lesson_create(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You do not have permission to add lessons to this course.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    if current_user.role == 'student':
        flash('Students cannot add lessons.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    form = LessonForm()
    
    if form.validate_on_submit():
        lesson = Lesson(
            title=form.title.data,
            content=form.content.data,
            file_url=form.file_url.data or None,
            order=int(form.order.data),
            course=course
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        flash('Lesson added successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
    
    # Set default order value
    if request.method == 'GET':
        last_lesson = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.order.desc()).first()
        form.order.data = '1' if not last_lesson else str(last_lesson.order + 1)
    
    return render_template('lessons/create.html', form=form, course=course)

@app.route('/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
def lesson_edit(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You do not have permission to edit this lesson.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    if current_user.role == 'student':
        flash('Students cannot edit lessons.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    form = LessonForm()
    
    if request.method == 'GET':
        form.title.data = lesson.title
        form.content.data = lesson.content
        form.file_url.data = lesson.file_url
        form.order.data = str(lesson.order)
    
    if form.validate_on_submit():
        lesson.title = form.title.data
        lesson.content = form.content.data
        lesson.file_url = form.file_url.data or None
        lesson.order = int(form.order.data)
        
        db.session.commit()
        
        flash('Lesson updated successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
    
    return render_template('lessons/edit.html', form=form, lesson=lesson, course=course)

@app.route('/lessons/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    
    # Kiểm tra quyền truy cập
    if current_user.role == 'student':
        # Sinh viên phải đăng ký khóa học để xem bài giảng
        if course not in current_user.student_profile.enrolled_courses:
            flash('You must be enrolled in this course to view lessons.', 'danger')
            return redirect(url_for('course_detail', course_id=course.id))
    elif current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        # Giáo viên chỉ có thể xem bài giảng của khóa học do họ dạy
        if not current_user.is_admin():
            flash('You do not have permission to view this lesson.', 'danger')
            return redirect(url_for('course_detail', course_id=course.id))
    
    # Lấy danh sách tất cả bài giảng trong khóa học
    course_lessons = course.lessons.order_by(Lesson.order).all()
    
    # Tìm bài giảng trước và sau
    prev_lesson = None
    next_lesson = None
    
    for i, current_lesson in enumerate(course_lessons):
        if current_lesson.id == lesson.id:
            if i > 0:
                prev_lesson = course_lessons[i-1]
            if i < len(course_lessons) - 1:
                next_lesson = course_lessons[i+1]
            break
    
    return render_template('lessons/detail.html', 
                           lesson=lesson, 
                           course_lessons=course_lessons,
                           prev_lesson=prev_lesson,
                           next_lesson=next_lesson)

# Assignment routes
@app.route('/courses/<int:course_id>/assignments/create', methods=['GET', 'POST'])
@login_required
def assignment_create(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You do not have permission to add assignments to this course.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    if current_user.role == 'student':
        flash('Students cannot add assignments.', 'danger')
        return redirect(url_for('course_detail', course_id=course.id))
    
    form = AssignmentForm()
    
    if form.validate_on_submit():
        # Combine date and time for deadline
        deadline_datetime = datetime.combine(form.deadline.data, form.deadline_time.data)
        
        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            deadline=deadline_datetime,
            course=course
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment added successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
    
    return render_template('assignments/create.html', form=form, course=course)

@app.route('/assignments/<int:assignment_id>')
def assignment_detail(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    course = assignment.course
    
    # For students, check if they have a submission
    submission = None
    if current_user.is_authenticated and current_user.is_student():
        submission = Submission.query.filter_by(
            assignment_id=assignment.id,
            student_id=current_user.student_profile.id
        ).first()
    
    # For instructors, get all submissions
    submissions = None
    if current_user.is_authenticated and (current_user.is_instructor() or current_user.is_admin()):
        submissions = assignment.submissions.all()
    
    return render_template('assignments/detail.html', 
                           assignment=assignment, 
                           course=course,
                           submission=submission,
                           submissions=submissions)

@app.route('/assignments/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
def assignment_edit(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    course = assignment.course
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You do not have permission to edit this assignment.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    if current_user.role == 'student':
        flash('Students cannot edit assignments.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    form = AssignmentForm()
    
    if request.method == 'GET':
        form.title.data = assignment.title
        form.description.data = assignment.description
        form.deadline.data = assignment.deadline.date()
        form.deadline_time.data = assignment.deadline.time()
    
    if form.validate_on_submit():
        # Combine date and time for deadline
        deadline_datetime = datetime.combine(form.deadline.data, form.deadline_time.data)
        
        assignment.title = form.title.data
        assignment.description = form.description.data
        assignment.deadline = deadline_datetime
        
        db.session.commit()
        
        flash('Assignment updated successfully!', 'success')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    return render_template('assignments/create.html', form=form, course=course, assignment=assignment)

# Submission routes
@app.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@role_required('student')
def submission_create(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if student is enrolled in the course
    if assignment.course not in current_user.student_profile.enrolled_courses:
        flash('You must be enrolled in the course to submit assignments.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    # Check if deadline has passed
    if assignment.deadline < datetime.utcnow():
        flash('The deadline for this assignment has passed.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    # Check if student already has a submission
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment.id,
        student_id=current_user.student_profile.id
    ).first()
    
    if existing_submission:
        flash('You have already submitted this assignment. Try editing your submission instead.', 'info')
        return redirect(url_for('submission_edit', submission_id=existing_submission.id))
    
    form = SubmissionForm()
    
    if form.validate_on_submit():
        submission = Submission(
            content=form.content.data,
            file_url=form.file_url.data or None,
            assignment=assignment,
            student=current_user.student_profile
        )
        
        db.session.add(submission)
        db.session.commit()
        
        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    return render_template('submissions/create.html', form=form, assignment=assignment)

@app.route('/submissions/<int:submission_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('student')
def submission_edit(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment
    
    # Check if this is the student's submission
    if submission.student_id != current_user.student_profile.id:
        flash('You can only edit your own submissions.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    # Check if deadline has passed
    if assignment.deadline < datetime.utcnow():
        flash('The deadline for this assignment has passed. You cannot edit your submission.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    form = SubmissionForm()
    
    if request.method == 'GET':
        form.content.data = submission.content
        form.file_url.data = submission.file_url
    
    if form.validate_on_submit():
        submission.content = form.content.data
        submission.file_url = form.file_url.data or None
        submission.submitted_at = datetime.utcnow()  # Update submission time
        
        db.session.commit()
        
        flash('Submission updated successfully!', 'success')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    return render_template('submissions/create.html', form=form, assignment=assignment, submission=submission)

@app.route('/submissions/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
def submission_grade(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment
    course = assignment.course
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You can only grade assignments for your own courses.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    if current_user.role == 'student':
        flash('Students cannot grade submissions.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    # Check if submission already has a grade
    existing_grade = Grade.query.filter_by(submission_id=submission.id).first()
    form = GradeForm()
    
    if request.method == 'GET' and existing_grade:
        form.score.data = existing_grade.score
        form.feedback.data = existing_grade.feedback
    
    if form.validate_on_submit():
        if existing_grade:
            # Update existing grade
            existing_grade.score = form.score.data
            existing_grade.feedback = form.feedback.data
            existing_grade.graded_at = datetime.utcnow()
        else:
            # Create new grade
            grade = Grade(
                score=form.score.data,
                feedback=form.feedback.data,
                submission=submission
            )
            db.session.add(grade)
        
        db.session.commit()
        
        flash('Submission graded successfully!', 'success')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    return render_template('submissions/detail.html', 
                           form=form, 
                           submission=submission, 
                           assignment=assignment,
                           course=course,
                           existing_grade=existing_grade)

# Schedule routes
@app.route('/courses/<int:course_id>/schedule', methods=['GET'])
def schedule_index(course_id):
    course = Course.query.get_or_404(course_id)
    schedules = Schedule.query.filter_by(course_id=course.id).order_by(Schedule.date, Schedule.start_time).all()
    
    # Group schedules by month for calendar view
    calendar_months = {}
    for schedule in schedules:
        month_key = schedule.date.strftime('%Y-%m')
        if month_key not in calendar_months:
            calendar_months[month_key] = []
        calendar_months[month_key].append(schedule)
    
    # Get upcoming schedules
    upcoming_schedules = Schedule.query.filter_by(course_id=course.id).filter(Schedule.date >= datetime.utcnow().date()).order_by(Schedule.date, Schedule.start_time).all()
    
    return render_template('schedule/index.html', 
                           course=course, 
                           schedules=schedules,
                           upcoming_schedules=upcoming_schedules,
                           calendar_months=calendar_months)

@app.route('/courses/<int:course_id>/schedule/create', methods=['GET', 'POST'])
@login_required
def schedule_create(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.instructor_profile.id:
        flash('You can only schedule classes for your own courses.', 'danger')
        return redirect(url_for('schedule_index', course_id=course.id))
    
    if current_user.role == 'student':
        flash('Students cannot schedule classes.', 'danger')
        return redirect(url_for('schedule_index', course_id=course.id))
    
    form = ScheduleForm()
    
    if form.validate_on_submit():
        schedule = Schedule(
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            topic=form.topic.data,
            location=form.location.data or None,
            course=course
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        flash('Class scheduled successfully!', 'success')
        return redirect(url_for('schedule_index', course_id=course.id))
    
    return render_template('schedule/index.html', form=form, course=course, create_mode=True)

# Admin user management routes
@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    users = User.query.all()
    return render_template('dashboard/admin.html', users=users, section='users')

@app.route('/admin/courses')
@login_required
@role_required('admin')
def admin_courses():
    courses = Course.query.all()
    instructors = Instructor.query.all()
    
    # Calculate some statistics for courses
    total_courses = len(courses)
    total_students_enrolled = sum(course.enrolled_students.count() for course in courses)
    avg_students_per_course = total_students_enrolled / total_courses if total_courses > 0 else 0
    courses_with_no_students = sum(1 for course in courses if course.enrolled_students.count() == 0)
    
    course_stats = {
        'total_courses': total_courses,
        'total_students_enrolled': total_students_enrolled,
        'avg_students_per_course': round(avg_students_per_course, 1),
        'courses_with_no_students': courses_with_no_students
    }
    
    return render_template('dashboard/admin.html', 
                          courses=courses, 
                          instructors=instructors, 
                          course_stats=course_stats,
                          section='courses')

@app.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_user_create():
    form = UserForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html', form=form, admin_mode=True)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'danger')
            return render_template('auth/register.html', form=form, admin_mode=True)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        
        # Set password (either custom or default)
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.set_password('changeme123')
            flash('User created with default password: changeme123', 'warning')
        
        db.session.add(user)
        db.session.flush()  # Needed to get user ID
        
        # Create profile based on role
        if form.role.data == 'student':
            profile = Student(
                user=user,
                full_name=form.full_name.data
            )
            db.session.add(profile)
        elif form.role.data == 'instructor':
            profile = Instructor(
                user=user,
                full_name=form.full_name.data,
                expertise=form.expertise.data
            )
            db.session.add(profile)
        
        db.session.commit()
        
        flash('User created successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('auth/register.html', form=form, admin_mode=True)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_user_edit(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm()
    
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        
        if user.is_student() and user.student_profile:
            form.full_name.data = user.student_profile.full_name
        elif user.is_instructor() and user.instructor_profile:
            form.full_name.data = user.instructor_profile.full_name
            form.expertise.data = user.instructor_profile.expertise
    
    if form.validate_on_submit():
        # Update user data
        user.username = form.username.data
        user.email = form.email.data
        
        # Handle password change if provided
        if form.password.data:
            user.set_password(form.password.data)
        
        # Check if role changed
        if user.role != form.role.data:
            # Handle role change
            old_role = user.role
            user.role = form.role.data
            
            # Create new profile if needed
            if form.role.data == 'student':
                if not user.student_profile:
                    profile = Student(
                        user=user,
                        full_name=form.full_name.data
                    )
                    db.session.add(profile)
                else:
                    user.student_profile.full_name = form.full_name.data
            elif form.role.data == 'instructor':
                if not user.instructor_profile:
                    profile = Instructor(
                        user=user,
                        full_name=form.full_name.data,
                        expertise=form.expertise.data
                    )
                    db.session.add(profile)
                else:
                    user.instructor_profile.full_name = form.full_name.data
                    user.instructor_profile.expertise = form.expertise.data
        else:
            # Just update existing profile
            if user.is_student() and user.student_profile:
                user.student_profile.full_name = form.full_name.data
            elif user.is_instructor() and user.instructor_profile:
                user.instructor_profile.full_name = form.full_name.data
                user.instructor_profile.expertise = form.expertise.data
        
        db.session.commit()
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('auth/register.html', form=form, admin_mode=True, user=user)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@role_required('admin')
def admin_user_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    
    # Reset password to default
    user.set_password('changeme123')
    db.session.commit()
    
    flash('Password reset successfully!', 'success')
    return redirect(url_for('admin_users'))
