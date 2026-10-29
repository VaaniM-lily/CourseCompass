# CourseCompass Project Report

## 1. Introduction

CourseCompass is a web-based course recommendation system that helps learners discover relevant online programs. It combines a polished course-catalog interface with a content-based recommendation engine built using TF-IDF and cosine similarity.

## 2. Problem Statement

Online learning catalogs contain thousands of courses. Learners often struggle to identify programs matching their interests, difficulty preference, and career goals. CourseCompass solves this through structured filtering and personalized recommendations.

## 3. Objectives

- Provide an intuitive course discovery platform.
- Support secure user registration and login.
- Collect learner preferences through onboarding.
- Recommend courses using TF-IDF and cosine similarity.
- Enable keyword search and multiple filters.
- Let users save and complete courses.
- Provide admin tools for dataset and course management.

## 4. System Architecture

CourseCompass uses a three-tier architecture:

1. Presentation layer: HTML, CSS, JavaScript, Jinja2 templates.
2. Application layer: Flask routes, authentication, search, recommendations, admin operations.
3. Data layer: SQLite database managed through Flask-SQLAlchemy.

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite, Flask-SQLAlchemy |
| Authentication | Flask-Login, Werkzeug |
| Data processing | Pandas |
| Machine learning | Scikit-learn |
| Frontend | HTML, CSS, JavaScript, Jinja2 |

## 6. Recommendation Model

Each course is represented as a text document combining its title, skills, and description. The text is vectorized using TF-IDF, which gives higher weight to distinctive and meaningful terms. Cosine similarity then compares course vectors; higher similarity indicates more closely related courses.

For personalized recommendations, the user’s interests, preferred difficulty, and learning goal are combined into a profile query. This query is compared with every course in the TF-IDF matrix.

## 7. Features Implemented

- Landing page with platform statistics.
- User registration and login.
- First registered user becomes administrator.
- Four-step onboarding quiz.
- Personalized course recommendations.
- Explore page with search, difficulty, institution, rating, sorting, and pagination filters.
- Course detail pages with direct Coursera enrollment links.
- Save, complete, and remove course actions.
- Dashboard with saved, completed, and recommended courses.
- Admin CSV upload with automatic data cleaning.
- Admin manual course addition and deletion.
- Admin user overview.

## 8. Data Processing

During CSV import, CourseCompass normalizes column names, removes blank titles and duplicates, cleans text, converts ratings to numeric values, standardizes difficulty labels, and rebuilds the TF-IDF matrix.

## 9. Security

Passwords are hashed using Werkzeug. Flask-Login manages user sessions and protects authenticated routes. Admin-only routes check the user’s administrator status.

## 10. Future Enhancements

- Collaborative filtering.
- Semantic embeddings.
- Course progress percentages.
- Email notifications.
- Cloud deployment.
- Analytics dashboard.
