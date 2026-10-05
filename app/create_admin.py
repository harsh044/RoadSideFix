from core.database import SessionLocal
from core.security import hash_password
from models.user import User, UserRole


def create_admin():
    db = SessionLocal()

    try:
        email = "admin@roadsidefix.com"

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("Admin already exists")
            return

        admin = User(
            name="RoadSide Fix Admin",
            email=email,
            phone="9999999999",
            hashed_password=hash_password("Admin@12345"),
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("Admin created successfully")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()