import argparse

from werkzeug.security import generate_password_hash

from flask_app import app
from app.extensions import db
from app.models import User


parser = argparse.ArgumentParser(description="Create or update an administrator user.")
parser.add_argument("email")
parser.add_argument("password")
args = parser.parse_args()

email = args.email.strip().lower()

with app.app_context():
    user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            password_hash=generate_password_hash(args.password),
            role="admin",
        )
        db.session.add(user)
        print(f"Created administrator: {email}")
    else:
        user.password_hash = generate_password_hash(args.password)
        user.role = "admin"
        print(f"Updated administrator: {email}")

    db.session.commit()
