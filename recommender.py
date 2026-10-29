import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def clean_text(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    if value.lower() in {"nan", "none", "null"}:
        return ""
    return re.sub(r"\s+", " ", value)


def normalize_level(value):
    value = clean_text(value).lower()
    mapping = {
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
        "conversant": "Conversant",
        "not calibrated": "Not Calibrated",
    }
    return mapping.get(value, clean_text(value) or "Not Calibrated")


def parse_skills(value):
    value = clean_text(value)
    if not value:
        return []
    parts = re.split(r"[,;\n\r|]+", value)
    return list(dict.fromkeys(p.strip() for p in parts if p.strip()))


def make_document(title, skills, description):
    title = clean_text(title)
    skills = clean_text(skills)
    description = clean_text(description)
    return f"{title} {title} {skills} {skills} {description}".strip()


class CourseRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=12000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )
        self.matrix = None
        self.course_ids = []

    def build(self, courses):
        if not courses:
            self.matrix = None
            self.course_ids = []
            return

        documents = [
            make_document(c.title, c.skills, c.description) for c in courses
        ]
        self.course_ids = [c.id for c in courses]
        self.matrix = self.vectorizer.fit_transform(documents)

    def recommend_from_course(self, course_id, limit=6):
        if self.matrix is None or course_id not in self.course_ids:
            return []

        index = self.course_ids.index(course_id)
        scores = cosine_similarity(self.matrix[index], self.matrix).ravel()

        results = []
        for i, score in enumerate(scores):
            candidate_id = self.course_ids[i]
            if candidate_id == course_id or score <= 0:
                continue
            results.append((candidate_id, float(score)))

        results.sort(key=lambda item: item[1], reverse=True)
        return results[:limit]

    def recommend_from_profile(
        self, interests, goal, preferred_level, minimum_rating, limit=8
    ):
        if self.matrix is None:
            return []

        profile_text = " ".join(
            clean_text(x)
            for x in [interests, goal, preferred_level]
            if clean_text(x)
        )

        if not profile_text:
            return []

        profile_vector = self.vectorizer.transform([profile_text])
        scores = cosine_similarity(profile_vector, self.matrix).ravel()

        results = []
        for i, score in enumerate(scores):
            if score <= 0:
                continue
            results.append((self.course_ids[i], float(score)))

        results.sort(key=lambda item: item[1], reverse=True)
        return results[:limit]


recommender = CourseRecommender()
