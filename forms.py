from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField, TimeField, FloatField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from datetime import datetime, date
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    # Role is now assigned as 'student' by default and can only be changed by admins
    expertise = StringField('Expertise (optional)', validators=[Optional(), Length(max=120)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please use a different username.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired()])
    course_image = FileField('Course Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Save Course')
    
    def validate_course_image(self, field):
        if field.data:
            filename = field.data.filename
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise ValidationError('Please upload an image file (PNG, JPG)')
            # Check file size
            field.data.seek(0, 2)  # Seek to end of file
            size = field.data.tell()  # Get size
            if size > 2 * 1024 * 1024:  # 2MB limit
                raise ValidationError('File size must be less than 2MB')

class LessonForm(FlaskForm):
    title = StringField('Lesson Title', validators=[DataRequired(), Length(max=120)])
    content = TextAreaField('Content', validators=[DataRequired()])
    file_url = StringField('File URL', validators=[Optional(), Length(max=255)])
    order = StringField('Order', validators=[DataRequired()])
    submit = SubmitField('Save Lesson')

class AssignmentForm(FlaskForm):
    title = StringField('Assignment Title', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired()])
    deadline = DateField('Deadline', validators=[DataRequired()], format='%Y-%m-%d')
    deadline_time = TimeField('Time', validators=[DataRequired()], format='%H:%M')
    submit = SubmitField('Save Assignment')
    
    def validate_deadline(self, deadline):
        if deadline.data < date.today():
            raise ValidationError('Deadline cannot be in the past.')

class SubmissionForm(FlaskForm):
    content = TextAreaField('Submission Content', validators=[Optional()])
    file_url = StringField('File URL', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Submit Assignment')

class GradeForm(FlaskForm):
    score = FloatField('Score', validators=[DataRequired()])
    feedback = TextAreaField('Feedback', validators=[Optional()])
    submit = SubmitField('Submit Grade')

class ScheduleForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = TimeField('Start Time', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time', validators=[DataRequired()], format='%H:%M')
    topic = StringField('Topic', validators=[DataRequired(), Length(max=120)])
    location = StringField('Location', validators=[Optional(), Length(max=120)])
    submit = SubmitField('Save Schedule')
    
    def validate_date(self, date):
        if date.data < datetime.now().date():
            raise ValidationError('Date cannot be in the past.')
    
    def validate_end_time(self, end_time):
        if self.start_time.data and end_time.data and end_time.data <= self.start_time.data:
            raise ValidationError('End time must be after start time.')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional()])
    password2 = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    role = SelectField('Role', choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')], validators=[DataRequired()])
    expertise = StringField('Expertise (for instructors)', validators=[Optional(), Length(max=120)])
    submit = SubmitField('Save User')
    
    def validate_password2(self, password2):
        if self.password.data and not password2.data:
            raise ValidationError('Please confirm your password.')
        if not self.password.data and password2.data:
            raise ValidationError('Please provide both password fields or leave them both empty.')

class ForumTopicForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=10)])
    is_pinned = BooleanField('Pin Topic')  # Chỉ giảng viên được quyền ghim bài
    submit = SubmitField('Post Topic')

class ForumResponseForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=2)])
    submit = SubmitField('Post Response')
