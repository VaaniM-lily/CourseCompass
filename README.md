# CourseCompass

CourseCompass is a Python-based course discovery web application. Users can register, complete a four-step onboarding quiz, explore and filter courses, save or complete courses, and receive personalized TF-IDF based recommendations.

## Tech Stack

- Python, Flask, Flask-SQLAlchemy, Flask-Login
- SQLite
- Pandas
- Scikit-learn
- HTML, CSS, JavaScript, Jinja2

## Run the Project

```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

The first registered user automatically becomes the administrator. Log in, open `/admin`, and upload the Coursera CSV dataset.

## Expected CSV Columns

`Course Name, University, Difficulty Level, Course Rating, Course URL, Course Description, Skills`

Common alternate names such as `title`, `institution`, `difficulty`, `rating`, `url`, `description`, and `skills` are also supported.

## Features

- Landing page
- Registration and login
- Four-step onboarding quiz
- Personalized TF-IDF recommendations
- Course search and filtering
- Course detail pages with Coursera enrollment links
- Saved and completed course dashboard
- Admin CSV upload and course management
