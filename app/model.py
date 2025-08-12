from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from app import db  # Ensure db is properly initialized in __init__.py

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'facilitator' or 'learner'
    is_admin = db.Column(db.Boolean, default=False)  # Admin flag
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}, Role: {self.role}, Admin: {self.is_admin}>"

class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(300), nullable=True)  # Now optional
    youtube_link = db.Column(db.String(300), nullable=True)  # New field
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User
    uploader = db.relationship('User', backref='tutorials')  # Relationship to User


    def __repr__(self):
        return f"<Tutorial {self.title}, Category: {self.category}, Uploaded by User ID: {self.uploaded_by}>"




class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorial.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # For replies
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    user = db.relationship('User', backref='comments')  # Add this relationship
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Comment {self.text[:20]} by User {self.user_id}>"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(300), nullable=False)  # Path to the uploaded image file
    whatsapp_link = db.Column(db.String(300), nullable=False)  # Link to contact via WhatsApp
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User ID of the seller

    def __repr__(self):
        return f"<Product {self.name}, Seller ID: {self.user_id}, Image: {self.image_filename}>"


# Notification model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(256), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    comment_id = db.Column(db.Integer, nullable=True)  # For direct comment linking

# Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='orders')
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='orders_placed')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='orders_received')

    def __repr__(self):
        return f"<Order {self.id} - Product {self.product_id} - Buyer {self.buyer_id} - Seller {self.seller_id} - Status {self.status}>"
