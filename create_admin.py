from app import app, db
from app.model import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if the admin user already exists
    admin_user = User.query.filter_by(email="admin1@gmail.com").first()
    if admin_user:
        # Update existing admin user
        admin_user.username = "admin"
        admin_user.role = "admin"
        admin_user.is_admin = True
        admin_user.password_hash = generate_password_hash("harbaytech001")
        print("Admin user updated!")
    else:
        # Create a new admin user
        admin_user = User(
            username="admin",
            email="admin1@gmail.com",
            role="admin",
            is_admin=True
        )
        admin_user.password_hash = generate_password_hash("harbaytech001")
        db.session.add(admin_user)
        print("Admin account created!")
    db.session.commit()

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"User: {user.username}, Email: {user.email}, is_admin: {user.is_admin}")
