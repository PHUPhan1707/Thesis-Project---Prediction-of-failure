"""Quick DB inspection for student 1519 in FM101 course."""
import os
import sys
import mysql.connector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "4000")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)

USER_ID = 1519
COURSE_ID = "course-v1:DHQG-HCM+FM101+2025_S2"

cur = conn.cursor(dictionary=True)
print("=" * 70)
print("1) student_features:")
cur.execute(
    "SELECT user_id, course_id, mooc_grade_percentage, h5p_avg_score, "
    "mooc_completion_rate, overall_completion "
    "FROM student_features WHERE user_id=%s AND course_id=%s",
    (USER_ID, COURSE_ID),
)
for r in cur.fetchall():
    print(r)

print("=" * 70)
print("2) mooc_grades:")
cur.execute(
    "SELECT user_id, course_id, grade_percentage, letter_grade, is_passed, email "
    "FROM mooc_grades WHERE user_id=%s AND course_id=%s",
    (USER_ID, COURSE_ID),
)
for r in cur.fetchall():
    print(r)

print("=" * 70)
print("3) raw_data (mooc fields if any):")
try:
    cur.execute(
        "SELECT user_id, course_id, mooc_grade_percentage, mooc_letter_grade, mooc_is_passed "
        "FROM raw_data WHERE user_id=%s AND course_id=%s LIMIT 5",
        (USER_ID, COURSE_ID),
    )
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print(f"raw_data query error: {e}")

cur.close()
conn.close()
