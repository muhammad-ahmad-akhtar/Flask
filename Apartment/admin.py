from app import db, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
hashed_password = bcrypt.generate_password_hash("admin").decode("utf-8")

new_user = User(username="admin", password=hashed_password)
db.session.add(new_user)
db.session.commit()

print("Admin user created successfully!")
