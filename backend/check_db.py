import sys
import logging
import pandas as pd
from db import fetch_all

print("--- Enrollment Counts ---")
enrollments = fetch_all("SELECT course_id, course_name, COUNT(*) as c FROM enrollments GROUP BY course_id, course_name")
for e in enrollments:
    print(f"{e['course_id']} | {e['course_name']} : {e['c']} students")

print("\n--- Raw Data Counts ---")
raw = fetch_all("SELECT course_id, COUNT(*) as c FROM raw_data GROUP BY course_id")
for r in raw:
    print(f"{r['course_id']} : {r['c']} students")

print("\n--- Student Feature Counts ---")
features = fetch_all("SELECT course_id, COUNT(*) as c FROM student_features GROUP BY course_id")
for f in features:
    print(f"{f['course_id']} : {f['c']} students")

print("\n--- Prediction Counts ---")
preds = fetch_all("SELECT course_id, model_name, COUNT(*) as c FROM predictions WHERE is_latest = 1 GROUP BY course_id, model_name")
for p in preds:
    print(f"{p['course_id']} | {p['model_name']} : {p['c']} students")
