import os
import sys
from app import app, db
from models import User, Student, Instructor

def create_test_users():
    """Create test users for different roles"""
    with app.app_context():
        # Check if users already exist
        # if User.query.filter_by(username='student1').first():
        #     print("Test users already exist. No changes made.")
        #     return
        
        # Create student user
        student_user = User(
            username='student',
            email='student@example.com',
            role='student'
        )
        student_user.set_password('a123')
        db.session.add(student_user)
        db.session.flush()  # To get the id
        
        # Create student profile
        student = Student(
            user_id=student_user.id,
            full_name='Student User'
        )
        db.session.add(student)
        
        # Create instructor user
        instructor_user = User(
            username='instructor',
            email='instructor@example.com',
            role='instructor'
        )
        instructor_user.set_password('a123')
        db.session.add(instructor_user)
        db.session.flush()  # To get the id
        
        # Create instructor profile
        instructor = Instructor(
            user_id=instructor_user.id,
            full_name='Instructor User',
            expertise='Computer Science'
        )
        db.session.add(instructor)
        
        # Create admin user
        admin_user = User(
            username='admin1',
            email='admin@example.com',
            role='admin'
        )
        admin_user.set_password('a123')
        db.session.add(admin_user)
        
        # Commit all changes
        db.session.commit()
        
        print("Created test users:")
        print("Student: username=student, password=a123")
        print("Instructor: username=instructor, password=a123")
        print("Admin: username=admin, password=a123")

if __name__ == '__main__':
    create_test_users()