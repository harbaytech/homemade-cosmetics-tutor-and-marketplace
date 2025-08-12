from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=150, message="Username must be between 3 and 150 characters.")
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Login')

class TutorialForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(), 
        Length(max=200, message="Title must not exceed 200 characters.")
    ])
    category = SelectField('Category', choices=[
        ('skincare', 'Skincare'),
        ('haircare', 'Haircare'),
        ('soapmaking', 'Soap Making'),
        ('others', 'Others')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[
        DataRequired(), 
        Length(max=500, message="Description must not exceed 500 characters.")
    ])
    file = FileField('Upload PDF', validators=[Optional()])
    youtube_link = StringField('YouTube Video Link', validators=[Optional(), URL(message="Enter a valid URL.")])
    submit = SubmitField('Upload')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[
        DataRequired(), 
        Length(max=150, message="Product name must not exceed 150 characters.")
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(), 
        Length(max=500, message="Description must not exceed 500 characters.")
    ])
    image = FileField('Upload Product Image', validators=[DataRequired()])
    whatsapp_link = StringField('WhatsApp Contact Link', validators=[
        DataRequired(), 
        URL(message="Enter a valid URL.")
    ])
    submit = SubmitField('Upload Product')