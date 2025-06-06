import os
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import app, db
from models import User, Student, Instructor, Course, Lesson, Assignment, Submission, Grade, Schedule, Enrollment, ForumTopic, ForumResponse, ForumLike
from forms import (LoginForm, RegistrationForm, CourseForm, LessonForm, AssignmentForm, 
                  SubmissionForm, GradeForm, ScheduleForm, UserForm, ForumTopicForm, ForumResponseForm)
from utils import role_required, get_submission

import logging
from werkzeug.utils import secure_filename

# Configure file upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'courses')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

logging.basicConfig(level=logging.DEBUG)

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
    student = current_user.student_profile
    
    # Get enrolled courses
    enrolled_courses = [e.course for e in student.enrollments if e.status == 'approved']
    
    # Calculate statistics
    total_completed_courses = 0
    total_hours = 0
    total_assignments_completed = 0
    total_score = 0
    total_graded = 0
    
    for course in enrolled_courses:
        assignments = Assignment.query.filter_by(course_id=course.id).all()
        for assignment in assignments:
            submission = Submission.query.filter_by(
                student_id=student.id,
                assignment_id=assignment.id
            ).first()
            
            if submission:
                total_assignments_completed += 1
                if submission.grade:
                    total_score += submission.grade.score
                    total_graded += 1
        
        # Estimate hours based on lessons and assignments
        lessons_count = course.lessons.count()
        assignments_count = len(assignments)
        # Assume average 1 hour per lesson and 2 hours per assignment
        course_hours = (lessons_count * 1) + (assignments_count * 2)
        total_hours += course_hours
        
        # Check if course is completed (all assignments submitted and graded)
        if assignments and total_assignments_completed == len(assignments):
            total_completed_courses += 1
    
    # Calculate average score
    avg_score = total_score / total_graded if total_graded > 0 else 0
    
    # Get pending enrollments
    pending_enrollments = [e.course for e in student.enrollments if e.status == 'pending']
    
    # Get recommended courses
    recommended_courses = Course.query.filter(
        ~Course.id.in_([c.id for c in enrolled_courses + pending_enrollments])
    ).limit(3).all()
    
    return render_template('dashboard/student.html',
                         student=student,
                         enrolled_courses=enrolled_courses,
                         pending_enrollments=pending_enrollments,
                         recommended_courses=recommended_courses,
                         total_completed_courses=total_completed_courses,
                         total_hours=total_hours,
                         avg_score=avg_score)

@app.route('/student/courses')
@login_required
@role_required('student')
def student_courses():
    # Get student profile
    student = current_user.student_profile
    # Get enrolled courses (approved only)
    enrolled_courses = [enrollment.course for enrollment in student.enrollments if enrollment.status == 'approved']
    # Get pending enrollments
    pending_enrollments = [enrollment for enrollment in student.enrollments if enrollment.status == 'pending']
    # Get recommended courses (courses not enrolled in)
    enrolled_course_ids = [c.id for c in enrolled_courses]
    pending_course_ids = [e.course.id for e in pending_enrollments]
    excluded_ids = enrolled_course_ids + pending_course_ids
    recommended_courses = Course.query.filter(~Course.id.in_(excluded_ids)).limit(3).all()
    return render_template('courses/student_courses.html',
                          student=student,
                          enrolled_courses=enrolled_courses,
                          pending_enrollments=pending_enrollments,
                          recommended_courses=recommended_courses)

@app.route('/dashboard/instructor')
@login_required
@role_required('instructor')
def instructor_dashboard():
    # Get instructor profile
    instructor = current_user.instructor_profile
    
    # Get instructor's courses
    courses = instructor.courses.all()
    
    # Get assignments data
    recent_assignments = []
    submissions_needing_grading = []
    course_stats = {}
    
    for course in courses:
        # Get recent assignments for this course
        course_assignments = Assignment.query.filter_by(course_id=course.id)\
            .order_by(Assignment.deadline.desc()).limit(3).all()
        for assignment in course_assignments:
            assignment.course_name = course.name  # Add course name for display
        recent_assignments.extend(course_assignments)
        
        # Get submissions needing grading
        for assignment in course.assignments:
            ungraded_submissions = Submission.query.filter_by(assignment_id=assignment.id)\
                .filter(~Submission.grade.has())\
                .all()
            for submission in ungraded_submissions:
                submissions_needing_grading.append(submission)
        
        # Calculate course statistics
        enrolled_students = [e for e in course.enrollments if e.status == 'approved']
        course_stats[course.id] = {
            'student_count': len(enrolled_students),
            'assignment_count': len(course.assignments.all()),
            'completion_rate': calculate_completion_rate(course)
        }
    
    # Sort submissions by submission date
    submissions_needing_grading.sort(key=lambda x: x.submitted_at, reverse=True)
    
    # Get upcoming schedules
    upcoming_schedules = []
    for course in courses:
        schedules = Schedule.query.filter_by(course_id=course.id)\
            .filter(Schedule.date >= datetime.utcnow().date())\
            .order_by(Schedule.date, Schedule.start_time).all()
        upcoming_schedules.extend(schedules)
    
    return render_template('dashboard/instructor.html', 
                         instructor=instructor,
                         courses=courses,
                         recent_assignments=recent_assignments,
                         submissions_needing_grading=submissions_needing_grading,
                         course_stats=course_stats,
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
    
    # Check if admin_settings route exists
    has_admin_settings = 'admin_settings' in current_app.view_functions
    
    return render_template('dashboard/admin.html', 
                           user_count=user_count,
                           student_count=student_count,
                           instructor_count=instructor_count,
                           course_count=course_count,
                           recent_users=recent_users,
                           courses=courses,
                           has_admin_settings=has_admin_settings)

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
    
    # Check enrollment status for students
    is_enrolled = False
    enrollment_status = None
    enrollment_date = None
    if current_user.is_authenticated and current_user.is_student():
        enrollment = Enrollment.query.filter_by(student_id=current_user.student_profile.id, course_id=course.id).first()
        if enrollment:
            enrollment_status = enrollment.status
            enrollment_date = enrollment.enrolled_at
            is_enrolled = enrollment.status == 'approved'
    
    return render_template('courses/detail.html', 
                           course=course, 
                           lessons=lessons, 
                           assignments=assignments,
                           schedules=schedules,
                           is_enrolled=is_enrolled,
                           Course=Course,
                           ForumTopic=ForumTopic,
                           now=datetime.now())

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_course_image(form_image):
    """Save a course image file and return the relative path for database storage.
    
    Args:
        form_image: FileStorage object from Flask request.files
        
    Returns:
        str: Relative path to saved image, or None if save failed
        
    Raises:
        Exception: If file is invalid or save fails
    """
    if not form_image or not form_image.filename:
        return None

    if not allowed_file(form_image.filename):
        raise Exception("Invalid file type. Only JPG and PNG allowed.")

    try:
        # Verify mimetype and basic image validation
        if not form_image.content_type.startswith('image/'):
            raise Exception("File must be an image")

        # Read file content safely
        form_image.seek(0)
        file_content = form_image.read()
        content_size = len(file_content)

        if content_size == 0:
            app.logger.error("Uploaded file is empty")
            raise Exception("Empty file uploaded") 

        if content_size > 2 * 1024 * 1024:  # 2MB limit
            raise Exception("File size exceeds 2MB limit")

        # Create unique filename with timestamp
        filename = secure_filename(form_image.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        new_filename = f"{timestamp}_{filename}"
        
        # Ensure upload directory exists
        upload_dir = os.path.join(app.static_folder, 'uploads', 'courses')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        
        # Save file with explicit binary mode
        filepath = os.path.join(upload_dir, new_filename)
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        # Verify saved file
        if not os.path.exists(filepath):
            raise Exception("File failed to save")
            
        saved_size = os.path.getsize(filepath)
        if saved_size == 0:
            os.remove(filepath)
            raise Exception("Saved file is empty")
            
        if saved_size != content_size:
            os.remove(filepath) 
            raise Exception("File corrupted during save")

        app.logger.info(f"Successfully saved image {new_filename} ({content_size} bytes)")
        return f'uploads/courses/{new_filename}'
        
    except Exception as e:
        app.logger.error(f"Error saving course image: {str(e)}")
        # Clean up file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        raise

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
            
            # Handle image upload
            image_path = None
            if 'course_image' in request.files:
                file = request.files['course_image']
                if file.filename:
                    try:
                        image_path = save_course_image(file)
                        if not image_path:
                            flash('Failed to save course image - unknown error.', 'danger')
                            return render_template('courses/create.html', form=form, instructors=instructors)
                    except Exception as e:
                        flash(str(e), 'danger')
                        return render_template('courses/create.html', form=form, instructors=instructors)
            
            # Create the course
            course = Course(
                name=form.name.data,
                description=form.description.data,
                image_url=image_path,
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
    
    # Check if user is instructor of this course or admin
    if not current_user.is_admin() and (not current_user.is_instructor() or 
        current_user.instructor_profile.id != course.instructor_id):
        flash('You do not have permission to edit this course.', 'danger')
        return redirect(url_for('course_detail', course_id=course_id))
    
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        try:
            file = request.files.get('course_image')
            if file and file.filename:
                # Save new image first to validate it
                try:
                    image_path = save_course_image(file)
                    if not image_path:
                        flash('Failed to save new image - unknown error.', 'danger')
                        return render_template('courses/edit.html', form=form, course=course)

                    # Only delete old image after successfully saving new one
                    if course.image_url:
                        old_image_path = os.path.join(app.static_folder, course.image_url)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                            except Exception as e:
                                app.logger.error(f"Error removing old image (not critical): {str(e)}")

                    course.image_url = image_path
                except Exception as e:
                    flash(str(e), 'danger')
                    return render_template('courses/edit.html', form=form, course=course)
            
            course.name = form.name.data
            course.description = form.description.data
            db.session.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('course_detail', course_id=course.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating course: {str(e)}', 'danger')
            return redirect(request.url)
            
    return render_template('courses/edit.html', form=form, course=course)

@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
@role_required('student')
def course_enroll(course_id):
    course = Course.query.get_or_404(course_id)
    student = current_user.student_profile
      # Kiểm tra đã có yêu cầu chưa
    existing = Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first()
    if existing:
        if existing.status == 'approved':
            flash('You are already enrolled in this course.', 'info')
        elif existing.status == 'pending':
            flash('Your enrollment request is pending approval.', 'info')
        elif existing.status == 'rejected':
            flash('Your previous enrollment request was rejected.', 'warning')
    else:
        # Tạo yêu cầu mới
        enrollment = Enrollment(student_id=student.id, course_id=course.id, status='pending')
        db.session.add(enrollment)
        db.session.commit()
        flash('Enrollment request sent. Please wait for instructor approval.', 'success')
    return redirect(url_for('course_detail', course_id=course.id))

@app.route('/courses/<int:course_id>/unenroll', methods=['POST'])
@login_required
@role_required('student')
def course_unenroll(course_id):
    course = Course.query.get_or_404(course_id)
    student = current_user.student_profile
    enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=course.id, status='approved').first()
    if enrollment:
        db.session.delete(enrollment)
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
        enrollment = Enrollment.query.filter_by(student_id=current_user.student_profile.id, course_id=course.id, status='approved').first()
        if not enrollment:
            flash('You must be enrolled in the course to view lessons.', 'danger')
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
                           submissions=submissions,
                           now=datetime.now())

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
    enrollment = Enrollment.query.filter_by(student_id=current_user.student_profile.id, course_id=assignment.course.id, status='approved').first()
    if not enrollment:
        flash('You must be enrolled in the course to submit assignments.', 'danger')
        return redirect(url_for('assignment_detail', assignment_id=assignment.id))
    
    # Check if deadline has passed
    if assignment.deadline < datetime.utcnow():
        flash('The deadline for this assignment has passed.', 'danger', 'persistent')
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
    
    return render_template('submissions/create.html', 
                           form=form, 
                           assignment=assignment,
                           now=datetime.now())

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
        flash('The deadline for this assignment has passed. You cannot edit your submission.', 'danger', 'persistent')
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
    
    return render_template('submissions/create.html', 
                           form=form, 
                           assignment=assignment, 
                           submission=submission,
                           now=datetime.now())

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
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()

    query = User.query

    if search_query:
        query = query.filter(User.username.ilike(f'%{search_query}%') | User.email.ilike(f'%{search_query}%'))

    if role_filter and role_filter in ['student', 'instructor', 'admin']:
        query = query.filter_by(role=role_filter)

    users = query.all()

    logging.debug(f"Search Query: {search_query}")
    logging.debug(f"Role Filter: {role_filter}")
    logging.debug(f"Filtered Users: {[user.username for user in users]}")

    has_admin_settings = 'admin_settings' in current_app.view_functions

    return render_template('dashboard/admin.html', 
                           users=users, 
                           section='users',
                           has_admin_settings=has_admin_settings)

@app.route('/admin/courses')
@login_required
@role_required('admin')
def admin_courses():
    search_query = request.args.get('search', '').strip()

    if search_query:
        courses = Course.query.filter(Course.name.ilike(f'%{search_query}%')).all()
    else:
        courses = Course.query.all()

    instructors = Instructor.query.all()

    total_courses = len(courses)
    total_students_enrolled = sum(len([e for e in course.enrollments if e.status == 'approved']) for course in courses)
    avg_students_per_course = total_students_enrolled / total_courses if total_courses > 0 else 0
    courses_with_no_students = sum(1 for course in courses if len([e for e in course.enrollments if e.status == 'approved']) == 0)

    course_stats = {
        'total_courses': total_courses,
        'total_students_enrolled': total_students_enrolled,
        'avg_students_per_course': round(avg_students_per_course, 1),
        'courses_with_no_students': courses_with_no_students
    }

    has_admin_settings = 'admin_settings' in current_app.view_functions

    return render_template('dashboard/admin.html', 
                          courses=courses, 
                          instructors=instructors, 
                          course_stats=course_stats,
                          section='courses',
                          has_admin_settings=has_admin_settings)


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

    # If user is an instructor, check if they have any courses
    if user.is_instructor() and user.instructor_profile:
        courses = user.instructor_profile.courses.all()
        if courses:
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                flash('Cannot delete instructor - no admin found to transfer courses to.', 'danger')
                return redirect(url_for('admin_users'))
            
            # Create instructor profile for admin if doesn't exist
            if not admin.instructor_profile:
                admin_instructor = Instructor(user=admin, full_name=admin.username)
                db.session.add(admin_instructor)
                db.session.flush()  # To get the instructor_id
            
            # Transfer courses to admin
            for course in courses:
                course.instructor_id = admin.instructor_profile.id
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user: ' + str(e), 'danger')
    
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

# Enrollment Management Routes for Instructors
@app.route('/courses/<int:course_id>/enrollments')
@login_required
@role_required('instructor')
def manage_enrollments(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if instructor owns this course
    if course.instructor_id != current_user.instructor_profile.id and not current_user.is_admin():
        flash('You can only manage enrollments for your own courses.', 'danger')
        return redirect(url_for('instructor_courses'))
    
    # Get all enrollments for this course
    pending_enrollments = Enrollment.query.filter_by(course_id=course.id, status='pending').all()
    approved_enrollments = Enrollment.query.filter_by(course_id=course.id, status='approved').all()
    rejected_enrollments = Enrollment.query.filter_by(course_id=course.id, status='rejected').all()
    
    # Get all students for the add student dropdown
    all_students = Student.query.all()
    enrolled_student_ids = [e.student_id for e in approved_enrollments]
    available_students = [s for s in all_students if s.id not in enrolled_student_ids]
    
    return render_template('courses/manage_enrollments.html',
                         course=course,
                         pending_enrollments=pending_enrollments,
                         approved_enrollments=approved_enrollments,
                         rejected_enrollments=rejected_enrollments,
                         available_students=available_students)

@app.route('/enrollments/<int:enrollment_id>/approve', methods=['POST'])
@login_required
@role_required('instructor')
def approve_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    course = enrollment.course
    
    # Check if instructor owns this course
    if course.instructor_id != current_user.instructor_profile.id and not current_user.is_admin():
        flash('You can only manage enrollments for your own courses.', 'danger')
        return redirect(url_for('instructor_courses'))
    
    enrollment.status = 'approved'
    enrollment.approved_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Approved enrollment for {enrollment.student.user.username}!', 'success')
    return redirect(url_for('manage_enrollments', course_id=course.id))

@app.route('/enrollments/<int:enrollment_id>/reject', methods=['POST'])
@login_required
@role_required('instructor')
def reject_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    course = enrollment.course
    
    # Check if instructor owns this course
    if course.instructor_id != current_user.instructor_profile.id and not current_user.is_admin():
        flash('You can only manage enrollments for your own courses.', 'danger')
        return redirect(url_for('instructor_courses'))
    
    enrollment.status = 'rejected'
    db.session.commit()
    
    flash(f'Rejected enrollment for {enrollment.student.user.username}.', 'info')
    return redirect(url_for('manage_enrollments', course_id=course.id))

@app.route('/courses/<int:course_id>/add-student', methods=['POST'])
@login_required
@role_required('instructor')
def add_student_to_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if instructor owns this course
    if course.instructor_id != current_user.instructor_profile.id and not current_user.is_admin():
        flash('You can only manage enrollments for your own courses.', 'danger')
        return redirect(url_for('instructor_courses'))
    
    student_id = request.form.get('student_id')
    if not student_id:
        flash('Please select a student.', 'warning')
        return redirect(url_for('manage_enrollments', course_id=course.id))
    
    student = Student.query.get_or_404(student_id)
    
    # Check if enrollment already exists
    existing_enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first()
    if existing_enrollment:
        if existing_enrollment.status == 'approved':
            flash(f'{student.user.username} is already enrolled in this course.', 'warning')
        elif existing_enrollment.status == 'pending':
            flash(f'{student.user.username} enrollment is already pending.', 'info')
        else:  # rejected
            # Change status to approved
            existing_enrollment.status = 'approved'
            existing_enrollment.approved_at = datetime.utcnow()
            db.session.commit()
            flash(f'Re-enrolled {student.user.username} in the course!', 'success')
    else:
        # Create new enrollment
        new_enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id,
            status='approved',
            enrolled_at=datetime.utcnow(),
            approved_at=datetime.utcnow()
        )
        db.session.add(new_enrollment)
        db.session.commit()
        flash(f'Added {student.user.username} to the course!', 'success')
    
    return redirect(url_for('manage_enrollments', course_id=course.id))

@app.route('/enrollments/<int:enrollment_id>/remove', methods=['POST'])
@login_required
@role_required('instructor')
def remove_student_from_course(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    course = enrollment.course
    
    # Check if instructor owns this course
    if course.instructor_id != current_user.instructor_profile.id and not current_user.is_admin():
        flash('You can only manage enrollments for your own courses.', 'danger')
        return redirect(url_for('instructor_courses'))
    
    student_name = enrollment.student.user.username
    db.session.delete(enrollment)
    db.session.commit()
    
    flash(f'Removed {student_name} from the course.', 'info')
    return redirect(url_for('manage_enrollments', course_id=course.id))

@app.route('/instructor/assignments')
@login_required
@role_required('instructor')
def instructor_assignments():
    instructor = current_user.instructor_profile
    courses = instructor.courses.all()
    
    # Get filter parameters
    selected_course = request.args.get('course', type=int)
    status = request.args.get('status')
    
    # Base query
    assignments_query = Assignment.query.join(Course).filter(Course.instructor_id == instructor.id)
    
    # Apply filters
    if selected_course:
        assignments_query = assignments_query.filter(Assignment.course_id == selected_course)
    
    if status:
        now = datetime.utcnow()
        if status == 'upcoming':
            assignments_query = assignments_query.filter(Assignment.deadline >= now)
        elif status == 'past':
            assignments_query = assignments_query.filter(Assignment.deadline < now)
    
    # Get all assignments
    assignments = assignments_query.order_by(Assignment.deadline).all()
    
    return render_template('assignments/instructor_assignments.html',
                          instructor=instructor,
                          courses=courses,
                          assignments=assignments,
                          selected_course=selected_course,
                          now=datetime.utcnow())

@app.route('/student/assignments')
@login_required
@role_required('student')
def student_assignments():
    student = current_user.student_profile
    enrolled_courses = [enrollment.course for enrollment in student.enrollments if enrollment.status == 'approved']
    
    # Get filter parameters
    selected_course = request.args.get('course', type=int)
    status = request.args.get('status')
    
    # Get assignments from enrolled courses
    course_ids = [course.id for course in enrolled_courses]
    assignments_query = Assignment.query.filter(Assignment.course_id.in_(course_ids))
    
    # Apply filters
    if selected_course:
        assignments_query = assignments_query.filter(Assignment.course_id == selected_course)
    
    if status:
        now = datetime.utcnow()
        if status == 'upcoming':
            assignments_query = assignments_query.filter(Assignment.deadline >= now)
        elif status == 'submitted':
            # Get assignments that have submissions from this student
            submitted_assignments = Submission.query.filter_by(student_id=student.id).with_entities(Submission.assignment_id)
            assignments_query = assignments_query.filter(Assignment.id.in_(submitted_assignments))
        elif status == 'missing':
            # Get assignments with passed deadline and no submission
            submitted_assignments = Submission.query.filter_by(student_id=student.id).with_entities(Submission.assignment_id)
            assignments_query = assignments_query.filter(Assignment.deadline < now)\
                .filter(~Assignment.id.in_(submitted_assignments))
        elif status == 'graded':
            # Get assignments that have graded submissions from this student
            graded_submissions = Submission.query.join(Grade)\
                .filter(Submission.student_id == student.id)\
                .with_entities(Submission.assignment_id)
            assignments_query = assignments_query.filter(Assignment.id.in_(graded_submissions))
    
    # Get all assignments
    assignments = assignments_query.order_by(Assignment.deadline).all()
    
    return render_template('assignments/student_assignments.html',
                          student=student,
                          enrolled_courses=enrolled_courses,
                          assignments=assignments,
                          selected_course=selected_course,
                          now=datetime.utcnow(),
                          get_submission=get_submission)

def calculate_completion_rate(course):
    """Calculate the completion rate for a course based on assignment submissions."""
    enrolled_students = [e for e in course.enrollments if e.status == 'approved']
    assignments = course.assignments.all()
    if not enrolled_students or not assignments:
        return 0
    
    total_possible = len(enrolled_students) * len(assignments)
    if total_possible == 0:
        return 0
        
    submitted_count = sum(
        1 for assignment in assignments
        for submission in assignment.submissions
        if submission.student_id in [e.student_id for e in enrolled_students]
    )
    
    return round((submitted_count / total_possible) * 100, 1)

# Forum routes
@app.route('/course/<int:course_id>/forum')
@login_required
def course_forum(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if user has access to this course
    if not current_user.is_admin():
        if current_user.is_instructor() and course.instructor_id != current_user.instructor_profile.id:
            abort(403)
        elif current_user.is_student() and not any(e.course_id == course_id and e.status == 'approved' for e in current_user.student_profile.enrollments):
            abort(403)
    
    # Get all topics for this course
    pinned_topics = ForumTopic.query.filter_by(course_id=course_id, is_pinned=True).order_by(ForumTopic.updated_at.desc()).all()
    regular_topics = ForumTopic.query.filter_by(course_id=course_id, is_pinned=False).order_by(ForumTopic.updated_at.desc()).all()
    
    return render_template('forum/index.html', course=course, pinned_topics=pinned_topics, regular_topics=regular_topics)

@app.route('/course/<int:course_id>/forum/new', methods=['GET', 'POST'])
@login_required
def new_forum_topic(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if user has access to this course
    if current_user.is_student() and not any(e.course_id == course_id and e.status == 'approved' for e in current_user.student_profile.enrollments):
        abort(403)
    
    form = ForumTopicForm()
    
    # Only instructors can pin topics
    if not current_user.is_instructor() and not current_user.is_admin():
        del form.is_pinned
    
    if form.validate_on_submit():
        topic = ForumTopic(
            title=form.title.data,
            content=form.content.data,
            course_id=course_id,
            author_id=current_user.id
        )
        
        if current_user.is_instructor() or current_user.is_admin():
            topic.is_pinned = form.is_pinned.data
        
        db.session.add(topic)
        db.session.commit()
        
        flash('Your topic has been posted!', 'success')
        return redirect(url_for('view_forum_topic', course_id=course_id, topic_id=topic.id))
    
    return render_template('forum/new_topic.html', form=form, course=course)

@app.route('/course/<int:course_id>/forum/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def view_forum_topic(course_id, topic_id):
    course = Course.query.get_or_404(course_id)
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Check if user has access to this course
    if not current_user.is_admin():
        if current_user.is_instructor() and course.instructor_id != current_user.instructor_profile.id:
            abort(403)
        elif current_user.is_student() and not any(e.course_id == course_id and e.status == 'approved' for e in current_user.student_profile.enrollments):
            abort(403)
    
    # Increment view count
    topic.view_count += 1
    db.session.commit()
    
    # Get all responses
    responses = ForumResponse.query.filter_by(topic_id=topic_id).order_by(ForumResponse.created_at).all()
    
    # Response form
    form = ForumResponseForm()
    if form.validate_on_submit() and not topic.is_locked:
        response = ForumResponse(
            content=form.content.data,
            topic_id=topic_id,
            author_id=current_user.id
        )
        
        db.session.add(response)
        db.session.commit()
        
        flash('Your response has been posted!', 'success')
        return redirect(url_for('view_forum_topic', course_id=course_id, topic_id=topic_id))
    
    return render_template('forum/view_topic.html', course=course, topic=topic, responses=responses, form=form)

@app.route('/forum/response/<int:response_id>/like', methods=['POST'])
@login_required
def like_forum_response(response_id):
    response = ForumResponse.query.get_or_404(response_id)
    topic = response.topic
    
    # Check if already liked
    existing_like = ForumLike.query.filter_by(response_id=response_id, user_id=current_user.id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        liked = False
    else:
        # Like
        like = ForumLike(response_id=response_id, user_id=current_user.id)
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    # For AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        like_count = ForumLike.query.filter_by(response_id=response_id).count()
        return jsonify({'liked': liked, 'count': like_count})
    
    # For regular requests
    return redirect(url_for('view_forum_topic', course_id=topic.course_id, topic_id=topic.id))

@app.route('/forum/response/<int:response_id>/mark-solution', methods=['POST'])
@login_required
def mark_solution(response_id):
    response = ForumResponse.query.get_or_404(response_id)
    topic = response.topic
    
    # Only instructor of the course or admin can mark solutions
    if not current_user.is_admin() and (not current_user.is_instructor() or topic.course.instructor_id != current_user.instructor_profile.id):
        abort(403)
    
    # Toggle solution status
    response.is_solution = not response.is_solution
    db.session.commit()
    
    # For AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'is_solution': response.is_solution})
    
    # For regular requests
    return redirect(url_for('view_forum_topic', course_id=topic.course_id, topic_id=topic.id))

@app.route('/course/<int:course_id>/forum/<int:topic_id>/toggle-lock', methods=['POST'])
@login_required
def toggle_topic_lock(course_id, topic_id):
    course = Course.query.get_or_404(course_id)
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Only instructor of the course or admin can lock/unlock topics
    if not current_user.is_admin() and (not current_user.is_instructor() or course.instructor_id != current_user.instructor_profile.id):
        abort(403)
    
    # Toggle locked status
    topic.is_locked = not topic.is_locked
    db.session.commit()
    
    flash(f"Topic {'locked' if topic.is_locked else 'unlocked'} successfully!", 'success')
    return redirect(url_for('view_forum_topic', course_id=course_id, topic_id=topic_id))

@app.route('/course/<int:course_id>/forum/<int:topic_id>/toggle-pin', methods=['POST'])
@login_required
def toggle_topic_pin(course_id, topic_id):
    course = Course.query.get_or_404(course_id)
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Only instructor of the course or admin can pin/unpin topics
    if not current_user.is_admin() and (not current_user.is_instructor() or course.instructor_id != current_user.instructor_profile.id):
        abort(403)
    
    # Toggle pinned status
    topic.is_pinned = not topic.is_pinned
    db.session.commit()
    
    flash(f"Topic {'pinned' if topic.is_pinned else 'unpinned'} successfully!", 'success')
    return redirect(url_for('course_forum', course_id=course_id))
@app.route('/instructor/students')
@login_required
@role_required('instructor')
def instructor_students():
    instructor = current_user.instructor_profile
    
    # Get all courses taught by this instructor and select first course for schedule link
    courses = instructor.courses.order_by(Course.created_at.desc()).all()
    first_course_id = courses[0].id if courses else None
    
    # Dictionary to store course and student info
    course_data = {}
    
    for course in courses:
        # Get all enrollments for this course
        enrollments = (Enrollment.query
                      .filter_by(course_id=course.id)
                      .order_by(Enrollment.status.desc(), Enrollment.enrolled_at.desc())
                      .all())
        
        # Get all assignments for this course
        assignments = (Assignment.query
                      .filter_by(course_id=course.id)
                      .order_by(Assignment.deadline)
                      .all())
        
        # Calculate student statistics for this course
        student_data = []
        total_submissions = 0
        total_grades = 0
        total_score = 0
        active_last_week = 0
        
        for enrollment in enrollments:
            student = enrollment.student
            student_active_last_week = False
            
            # Get student's submissions for this course's assignments
            submission_data = {}
            student_total_score = 0
            graded_assignments = 0
            submitted_count = 0
            
            last_activity = enrollment.enrolled_at
            
            for assignment in assignments:
                submission = Submission.query.filter_by(
                    student_id=student.id,
                    assignment_id=assignment.id
                ).first()
                
                # Update last activity if we have a more recent submission
                if submission:
                    if submission.submitted_at > last_activity:
                        last_activity = submission.submitted_at
                    
                    submitted_count += 1
                    grade = Grade.query.filter_by(submission_id=submission.id).first()
                    
                    if grade:
                        student_total_score += grade.score
                        graded_assignments += 1
                        total_grades += 1
                        total_score += grade.score
                    
                    # Check if submission was within last week
                    if (datetime.utcnow() - submission.submitted_at).days <= 7:
                        student_active_last_week = True
                
                if submission:
                    grade = Grade.query.filter_by(submission_id=submission.id).first()
                    submission_data[assignment.id] = {
                        'submitted': True,
                        'submitted_at': submission.submitted_at,
                        'grade': grade.score if grade else None,
                        'graded': True if grade else False
                    }
                else:
                    submission_data[assignment.id] = {
                        'submitted': False,
                        'submitted_at': None,
                        'grade': None,
                        'graded': False
                    }
            
            # Calculate student statistics
            avg_score = student_total_score / graded_assignments if graded_assignments > 0 else None
            completion_rate = (submitted_count / len(assignments)) * 100 if assignments else 0
            
            # Add student info to list
            student_data.append({
                'student': student,
                'enrolled_date': enrollment.enrolled_at,
                'status': enrollment.status,
                'submissions': submission_data,
                'average_score': avg_score,
                'completion_rate': completion_rate,
                'last_activity': last_activity,
                'submitted_count': submitted_count,
                'total_assignments': len(assignments),
                'total_graded': graded_assignments,
                'enrollment_id': enrollment.id  # Add enrollment ID for action buttons
            })
            
            total_submissions += submitted_count
            
            if student_active_last_week:
                active_last_week += 1
        
        # Calculate course-level statistics
        approved_enrollments = [e for e in enrollments if e.status == 'approved']
        course_avg_score = total_score / total_grades if total_grades > 0 else 0
        course_completion_rate = (total_submissions / (len(approved_enrollments) * len(assignments))) * 100 if approved_enrollments and assignments else 0
        
        # Store course data with statistics
        course_data[course.id] = {
            'course': course,
            'students': student_data,
            'assignments': assignments,
            'total_students': len(approved_enrollments),
            'total_pending': len([e for e in enrollments if e.status == 'pending']),
            'total_assignments': len(assignments),
            'total_submissions': total_submissions,
            'average_score': course_avg_score,
            'completion_rate': course_completion_rate,
            'active_last_week': active_last_week
        }
    
    return render_template('dashboard/instructor_students.html',
                         course_data=course_data,
                         instructor=instructor,
                         first_course_id=first_course_id,
                         now=datetime.utcnow(),
                         datetime=datetime)

@app.route('/instructor/student/<int:course_id>/<int:student_id>')
@login_required
@role_required('instructor')
def student_detail(course_id, student_id):
    instructor = current_user.instructor_profile
    course = Course.query.get_or_404(course_id)
    
    # Verify instructor owns this course
    if course.instructor_id != instructor.id:
        abort(403)
    
    student = Student.query.get_or_404(student_id)
    enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=student_id).first_or_404()
    
    # Get student's submissions and grades
    assignments = Assignment.query.filter_by(course_id=course_id).order_by(Assignment.deadline).all()
    submissions = []
    
    for assignment in assignments:
        submission = Submission.query.filter_by(
            student_id=student_id,
            assignment_id=assignment.id
        ).first()
        
        grade = None
        if submission:
            grade = Grade.query.filter_by(submission_id=submission.id).first()
        
        submissions.append({
            'assignment': assignment,
            'submission': submission,
            'grade': grade
        })
    
    return render_template('dashboard/student_detail.html',
                         course=course,
                         student=student,
                         enrollment=enrollment,
                         submissions=submissions,
                         now=datetime.utcnow())

@app.route('/instructor/course/<int:course_id>/student/<int:student_id>/submissions')
@login_required
@role_required('instructor')
def view_submissions(course_id, student_id):
    course = Course.query.get_or_404(course_id)
    student = Student.query.get_or_404(student_id)
    
    # Verify instructor owns this course
    if course.instructor_id != current_user.instructor_profile.id:
        abort(403)
    
    # Get all submissions for this student in this course
    submissions = (Submission.query
                  .join(Assignment)
                  .filter(Assignment.course_id == course_id,
                         Submission.student_id == student_id)
                  .order_by(Assignment.deadline.desc())
                  .all())
    
    return render_template('submissions/student_submissions.html',
                         course=course,
                         student=student,
                         submissions=submissions)

@app.route('/grade-submission/<int:submission_id>', methods=['GET', 'POST'])
@login_required
@role_required('instructor')
def grade_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment
    course = assignment.course
    
    # Verify instructor owns this course
    if course.instructor_id != current_user.instructor_profile.id:
        abort(403)
    
    if request.method == 'POST':
        score = request.form.get('score', type=float)
        feedback = request.form.get('feedback')
        
        if score is None or score < 0 or score > 100:
            flash('Please enter a valid score between 0 and 100', 'danger')
            return redirect(url_for('grade_submission', submission_id=submission_id))
        
        # Create or update grade
        grade = Grade.query.filter_by(submission_id=submission_id).first()
        if grade is None:
            grade = Grade(submission_id=submission_id, score=score, feedback=feedback)
            db.session.add(grade)
        else:
            grade.score = score
            grade.feedback = feedback
            grade.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Grade saved successfully', 'success')
        return redirect(url_for('student_detail', 
                              course_id=course.id,
                              student_id=submission.student_id))
    
    return render_template('submissions/grade.html',
                         submission=submission,
                         grade=Grade.query.filter_by(submission_id=submission_id).first())
