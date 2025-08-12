from app import app, db
from app.model import User, Product, Tutorial

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created!")

