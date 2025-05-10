from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Association table for many-to-many relationship between students and courses
enrollments = db.Table('enrollments',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    db.Column('enrollment_date', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'instructor', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False)
    instructor_profile = db.relationship('Instructor', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_instructor(self):
        return self.role == 'instructor'
    
    def is_student(self):
        return self.role == 'student'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    
    # Relationships
    enrolled_courses = db.relationship('Course', secondary=enrollments, backref=db.backref('enrolled_students', lazy='dynamic'))
    submissions = db.relationship('Submission', backref='student', lazy='dynamic')

class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    expertise = db.Column(db.String(120))
    
    # Relationships
    courses = db.relationship('Course', backref='instructor', lazy='dynamic')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_url = db.Column(db.String(255))
    
    # Relationships
    lessons = db.relationship('Lesson', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='course', lazy='dynamic', cascade='all, delete-orphan')

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(255))
    order = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_url = db.Column(db.String(255))
    content = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    # Relationships
    grade = db.relationship('Grade', backref='submission', uselist=False, cascade='all, delete-orphan')

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    graded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    topic = db.Column(db.String(120), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    location = db.Column(db.String(120))
