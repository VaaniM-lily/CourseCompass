import os
import re

import numpy as np
import pandas as pd
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)

from config import Config
from models import db, User, Course, UserCourse
from recommender import recommender, clean_text, normalize_level, parse_skills

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def rebuild_recommender():
    courses = Course.query.order_by(Course.id).all()
    recommender.build(courses)


def refresh_filter_options():
    levels = sorted(
        {c.difficulty for c in Course.query.with_entities(Course.difficulty).all() if c.difficulty}
    )
    universities = sorted(
        {c.university for c in Course.query.with_entities(Course.university).all() if c.university}
    )
    return levels, universities


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def import_csv(path, replace_existing=True):
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.astype(str).str.strip()

    aliases = {
        "title": ["course name", "course title", "name", "title"],
        "university": ["university", "institution", "organization"],
        "difficulty": ["difficulty level", "difficulty", "level"],
        "rating": ["course rating", "rating", "ratings"],
        "url": ["course url", "course_url", "url", "course link", "link"],
        "description": ["course description", "description", "about"],
        "skills": ["skills", "course skills", "skill"],
    }

    normalized = {
        re.sub(r"[^a-z0-9]+", " ", c.lower()).strip(): c
        for c in df.columns
    }

    rename_map = {}
    for target, options in aliases.items():
        if target in df.columns:
            continue
        for option in options:
            if option in normalized:
                rename_map[normalized[option]] = target
                break

    df = df.rename(columns=rename_map)

    required = ["title", "university", "difficulty", "rating", "url", "description", "skills"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for column in required:
        df[column] = df[column].map(clean_text)

    df = df[df["title"] != ""].copy()
    df = df.drop_duplicates(subset=required).reset_index(drop=True)

    df["rating"] = pd.to_numeric(
        df["rating"].replace(["Not Calibrated", "Not rated", "N/A", "NA", ""], np.nan),
        errors="coerce"
    )
    df.loc[~df["rating"].between(0, 5), "rating"] = np.nan
    df["difficulty"] = df["difficulty"].map(normalize_level)

    if replace_existing:
        UserCourse.query.delete()
        Course.query.delete()
        db.session.commit()

    added = 0
    for _, row in df.iterrows():
        course = Course(
            title=row["title"],
            university=row["university"],
            difficulty=row["difficulty"],
            rating=None if pd.isna(row["rating"]) else float(row["rating"]),
            url=row["url"],
            description=row["description"],
            skills=row["skills"],
        )
        db.session.add(course)
        added += 1

    db.session.commit()
    rebuild_recommender()
    return added


def search_courses(query, level, university, minimum_rating, sort_by, page, per_page):
    courses = Course.query

    query = clean_text(query).lower()
    if query:
        pattern = f"%{query}%"
        courses = courses.filter(
            db.or_(
                Course.title.ilike(pattern),
                Course.description.ilike(pattern),
                Course.skills.ilike(pattern),
                Course.university.ilike(pattern),
            )
        )

    if level and level != "Any":
        courses = courses.filter(Course.difficulty == level)

    if university and university != "Any":
        courses = courses.filter(Course.university == university)

    if minimum_rating and float(minimum_rating) > 0:
        courses = courses.filter(Course.rating >= float(minimum_rating))

    if sort_by == "highest":
        courses = courses.order_by(Course.rating.desc().nullslast(), Course.title.asc())
    elif sort_by == "lowest":
        courses = courses.order_by(Course.rating.asc().nullslast(), Course.title.asc())
    elif sort_by == "title":
        courses = courses.order_by(Course.title.asc())
    else:
        courses = courses.order_by(Course.rating.desc().nullslast(), Course.title.asc())

    return courses.paginate(page=page, per_page=per_page, error_out=False)


@app.context_processor
def inject_globals():
    return {"app_name": "CourseCompass"}


@app.route("/")
def landing():
    total_courses = Course.query.count()
    total_universities = Course.query.with_entities(Course.university).distinct().count()
    total_levels = Course.query.with_entities(Course.difficulty).distinct().count()

    return render_template(
        "landing.html",
        total_courses=total_courses,
        total_universities=total_universities,
        total_levels=total_levels,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = clean_text(request.form.get("name"))
        email = clean_text(request.form.get("email")).lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            user.is_admin = User.query.count() == 0
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to CourseCompass!", "success")
            return redirect(url_for("onboarding"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = clean_text(request.form.get("email")).lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("landing"))


@app.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if request.method == "POST":
        interests = request.form.getlist("interests")
        preferred_level = clean_text(request.form.get("preferred_level")) or "Any"
        minimum_rating = float(request.form.get("minimum_rating") or 0)
        learning_goal = clean_text(request.form.get("learning_goal"))

        current_user.interest_areas = ", ".join(interests)
        current_user.preferred_level = preferred_level
        current_user.minimum_rating = minimum_rating
        current_user.learning_goal = learning_goal
        current_user.onboarding_complete = True

        db.session.commit()
        flash("Your learning preferences have been saved.", "success")
        return redirect(url_for("dashboard"))

    return render_template("onboarding.html")


@app.route("/dashboard")
@login_required
def dashboard():
    saved = UserCourse.query.filter_by(user_id=current_user.id, status="saved").all()
    completed = UserCourse.query.filter_by(user_id=current_user.id, status="completed").all()

    recommendations = []
    if recommender.matrix is not None:
        raw = recommender.recommend_from_profile(
            current_user.interest_areas,
            current_user.learning_goal,
            current_user.preferred_level,
            current_user.minimum_rating,
            limit=6,
        )

        course_map = {
            course.id: course
            for course in Course.query.filter(
                Course.id.in_([item[0] for item in raw])
            ).all()
        } if raw else {}

        for course_id, score in raw:
            course = course_map.get(course_id)
            if course:
                recommendations.append({
                    "course": course,
                    "score": round(score * 100, 1),
                })

    return render_template(
        "dashboard.html",
        saved=saved,
        completed=completed,
        recommendations=recommendations,
    )


@app.route("/explore")
@login_required
def explore():
    levels, universities = refresh_filter_options()

    query = request.args.get("query", "")
    level = request.args.get("level", "Any")
    university = request.args.get("university", "Any")
    minimum_rating = request.args.get("minimum_rating", 0)
    sort_by = request.args.get("sort_by", "recommended")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 9, type=int)

    pagination = search_courses(
        query, level, university, minimum_rating, sort_by, page, per_page
    )

    saved_ids = {
        item.course_id for item in UserCourse.query.filter_by(
            user_id=current_user.id
        ).all()
    }

    return render_template(
        "explore.html",
        pagination=pagination,
        levels=levels,
        universities=universities,
        filters={
            "query": query,
            "level": level,
            "university": university,
            "minimum_rating": float(minimum_rating or 0),
            "sort_by": sort_by,
            "per_page": per_page,
        },
        saved_ids=saved_ids,
    )


@app.route("/course/<int:course_id>")
@login_required
def course_detail(course_id):
    course = db.get_or_404(Course, course_id)

    related = []
    if recommender.matrix is not None:
        raw = recommender.recommend_from_course(course.id, limit=4)
        course_map = {
            c.id: c for c in Course.query.filter(
                Course.id.in_([item[0] for item in raw])
            ).all()
        } if raw else {}

        for related_id, score in raw:
            related_course = course_map.get(related_id)
            if related_course:
                related.append({
                    "course": related_course,
                    "score": round(score * 100, 1),
                })

    user_course = UserCourse.query.filter_by(
        user_id=current_user.id, course_id=course.id
    ).first()

    return render_template(
        "course_detail.html",
        course=course,
        related=related,
        user_course=user_course,
        skills=parse_skills(course.skills),
    )


@app.route("/save-course/<int:course_id>", methods=["POST"])
@login_required
def save_course(course_id):
    course = db.get_or_404(Course, course_id)
    existing = UserCourse.query.filter_by(
        user_id=current_user.id, course_id=course.id
    ).first()

    if existing:
        existing.status = "saved"
    else:
        db.session.add(UserCourse(user_id=current_user.id, course_id=course.id))

    db.session.commit()
    flash("Course saved to your dashboard.", "success")
    return redirect(request.referrer or url_for("explore"))


@app.route("/complete-course/<int:course_id>", methods=["POST"])
@login_required
def complete_course(course_id):
    course = db.get_or_404(Course, course_id)
    existing = UserCourse.query.filter_by(
        user_id=current_user.id, course_id=course.id
    ).first()

    if existing:
        existing.status = "completed"
    else:
        db.session.add(UserCourse(
            user_id=current_user.id,
            course_id=course.id,
            status="completed"
        ))

    db.session.commit()
    flash("Course marked as completed.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/remove-course/<int:course_id>", methods=["POST"])
@login_required
def remove_course(course_id):
    UserCourse.query.filter_by(
        user_id=current_user.id, course_id=course_id
    ).delete()
    db.session.commit()
    flash("Course removed from your dashboard.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash("Admin access is required.", "error")
        return redirect(url_for("dashboard"))

    courses = Course.query.order_by(Course.title.asc()).all()
    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin.html", courses=courses, users=users)


@app.route("/admin/upload", methods=["POST"])
@login_required
def admin_upload():
    if not current_user.is_admin:
        flash("Admin access is required.", "error")
        return redirect(url_for("dashboard"))

    file = request.files.get("dataset")
    replace_existing = request.form.get("replace_existing") == "on"

    if not file or file.filename == "":
        flash("Please choose a CSV file.", "error")
        return redirect(url_for("admin"))

    if not allowed_file(file.filename):
        flash("Only CSV files are allowed.", "error")
        return redirect(url_for("admin"))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    try:
        added = import_csv(path, replace_existing=replace_existing)
        flash(f"Imported {added} courses successfully.", "success")
    except Exception as error:
        db.session.rollback()
        flash(f"Import failed: {error}", "error")

    return redirect(url_for("admin"))


@app.route("/admin/course/add", methods=["POST"])
@login_required
def admin_add_course():
    if not current_user.is_admin:
        flash("Admin access is required.", "error")
        return redirect(url_for("dashboard"))

    course = Course(
        title=clean_text(request.form.get("title")),
        university=clean_text(request.form.get("university")),
        difficulty=normalize_level(request.form.get("difficulty")),
        rating=float(request.form.get("rating") or 0) or None,
        url=clean_text(request.form.get("url")),
        description=clean_text(request.form.get("description")),
        skills=clean_text(request.form.get("skills")),
    )

    if not course.title:
        flash("Course title is required.", "error")
        return redirect(url_for("admin"))

    db.session.add(course)
    db.session.commit()
    rebuild_recommender()
    flash("Course added.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/course/delete/<int:course_id>", methods=["POST"])
@login_required
def admin_delete_course(course_id):
    if not current_user.is_admin:
        flash("Admin access is required.", "error")
        return redirect(url_for("dashboard"))

    course = db.get_or_404(Course, course_id)
    db.session.delete(course)
    db.session.commit()
    rebuild_recommender()
    flash("Course deleted.", "success")
    return redirect(url_for("admin"))


@app.route("/api/recommendations")
@login_required
def api_recommendations():
    if recommender.matrix is None:
        return jsonify({"recommendations": []})

    raw = recommender.recommend_from_profile(
        current_user.interest_areas,
        current_user.learning_goal,
        current_user.preferred_level,
        current_user.minimum_rating,
        limit=8,
    )

    courses = Course.query.filter(Course.id.in_([item[0] for item in raw])).all() if raw else []
    course_map = {course.id: course for course in courses}

    return jsonify({
        "recommendations": [
            {
                "id": course_id,
                "title": course_map[course_id].title,
                "university": course_map[course_id].university,
                "similarity": round(score * 100, 1),
            }
            for course_id, score in raw if course_id in course_map
        ]
    })


with app.app_context():
    db.create_all()
    rebuild_recommender()


if __name__ == "__main__":
    app.run(debug=True)
