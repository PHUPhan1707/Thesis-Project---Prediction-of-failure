"""
Lấy course_id thực tế từ database
"""
import mysql.connector

connection = mysql.connector.connect(
    host='localhost',
    port=4000,
    database='dropout_prediction_db',
    user='dropout_user',
    password='dropout_pass_123'
)

cursor = connection.cursor(dictionary=True)
cursor.execute("SELECT DISTINCT course_id FROM h5p_scores LIMIT 5")
courses = cursor.fetchall()

print("Course IDs trong database:")
for course in courses:
    print(f"  - {course['course_id']}")

cursor.close()
connection.close()
