"""Train TfidfVectorizer + MultinomialNB on spam_dataset.csv and persist with joblib.

Runs at IMAGE BUILD TIME (builder stage of the multi-stage Dockerfile), so the
runtime image ships only model.joblib -- never pandas, the CSV, or this script.
"""
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

df = pd.read_csv("spam_dataset.csv")
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

pipe = Pipeline(
    [
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)),
        ("nb", MultinomialNB(alpha=0.1)),
    ]
)
pipe.fit(X_train, y_train)

pred = pipe.predict(X_test)
print(f"holdout accuracy = {accuracy_score(y_test, pred):.4f}")
print(classification_report(y_test, pred, digits=4))

joblib.dump(pipe, "model.joblib")
print("wrote model.joblib")
