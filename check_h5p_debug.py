# -*- coding: utf-8 -*-
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}

print("Connecting to database...")
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)
print("Connected!")

print("\n1. CHECK H5P DATA")
print("="*60)
cursor.execute("SELECT COUNT(*) as cnt FROM h5p_scores")
result = cursor.fetchone()
print(f"Total H5P records: {result['cnt']}")

print("\n2. COURSES WITH H5P DATA")
print("="*60)
cursor.execute("""
    SELECT course_id, COUNT(*) as cnt
    FROM h5p_scores
    GROUP BY course_id
""")
for row in cursor.fetchall():
    print(f"Course: {row['course_id']} - Records: {row['cnt']}")

cursor.close()
conn.close()
print("\nDone!")
