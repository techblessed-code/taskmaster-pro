
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email


class TaskForm(FlaskForm):

    title = StringField(
        'Title',
        validators=[
            DataRequired(message='Title is required'),
            Length(min=3, max=100, message='Field must be between 3 and 100 characters')
        ]
    )

    description = TextAreaField(
        'Description',
        validators=[
            Length(max=300, message='Description cannot exceed 300 characters')
        ]
    )

    priority = SelectField(
        'Priority',
        choices=[
            ('low', 'Low'),
            ('high', 'High')
        ],
        validators=[DataRequired()]
    )

    due_date = DateField(
        'Due Date',
        format='%Y-%m-%d',
        validators=[DataRequired()]
    )

    attachment = FileField(
        'Attachment',
        validators=[
            FileAllowed(['jpg', 'png', 'pdf', 'doc', 'docx'], 'Images and documents only!')
        ]
    )


class ContactForm(FlaskForm):

    name = StringField(
        'Name',
        validators=[
            DataRequired(),
            Length(min=2, max=30)
        ]
    )

    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email()
        ]
    )

    message = TextAreaField(
        'Message',
        validators=[
            DataRequired(),
            Length(min=5, max=500)
        ]
    )
