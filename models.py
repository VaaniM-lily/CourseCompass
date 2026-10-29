from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    interest_areas = db.Column(db.Text, default="")
    preferred_level = db.Column(db.String(50), default="Any")
    minimum_rating = db.Column(db.Float, default=0.0)
    learning_goal = db.Column(db.Text, default="")
    onboarding_complete = db.Column(db.Boolean, default=False)

    saved_courses = db.relationship(
        "UserCourse", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    university = db.Column(db.String(200), default="")
    difficulty = db.Column(db.String(50), default="Not Calibrated")
    rating = db.Column(db.Float)
    url = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")
    skills = db.Column(db.Text, default="")

    saved_by = db.relationship(
        "UserCourse", back_populates="course", cascade="all, delete-orphan"
    )


class UserCourse(db.Model):
    __tablename__ = "user_courses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    status = db.Column(db.String(20), default="saved")
    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship("User", back_populates="saved_courses")
    course = db.relationship("Course", back_populates="saved_by")

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="unique_user_course"),
    )
