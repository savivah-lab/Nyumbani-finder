"""Usage: python -m scripts.create_admin 0712345678 "Full Name" """
import getpass
import sys

from app.database import Base, SessionLocal, engine
from app.models import Role, User
from app.security import hash_password
from app.utils import normalize_phone

Base.metadata.create_all(engine)
phone, name = normalize_phone(sys.argv[1]), sys.argv[2]
pw = getpass.getpass("Password (min 8 chars): ")
assert len(pw) >= 8, "Password too short"
with SessionLocal() as db:
    db.add(User(phone_number=phone, full_name=name, password_hash=hash_password(pw), role=Role.admin))
    db.commit()
print("Admin created:", phone)
