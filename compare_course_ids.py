"""
So sánh course_id giữa enrollments và h5p_scores
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

print("=" * 80)
print("COURSE_IDs trong ENROLLMENTS:")
print("=" * 80)
cursor.execute("SELECT DISTINCT course_id FROM enrollments")
enrollments_courses = cursor.fetchall()
for course in enrollments_courses:
    print(f"  - {course['course_id']}")

print("\n" + "=" * 80)
print("COURSE_IDs trong H5P_SCORES:")
print("=" * 80)
cursor.execute("SELECT DISTINCT course_id FROM h5p_scores")
h5p_courses = cursor.fetchall()
for course in h5p_courses:
    print(f"  - {course['course_id']}")

print("\n" + "=" * 80)
print("SO SÁNH:")
print("=" * 80)

enrollment_ids = {c['course_id'] for c in enrollments_courses}
h5p_ids = {c['course_id'] for c in h5p_courses}

print(f"\nCourse IDs chỉ có trong ENROLLMENTS (không có H5P data):")
for cid in enrollment_ids - h5p_ids:
    print(f"  - {cid}")

print(f"\nCourse IDs chỉ có trong H5P_SCORES (không có enrollment):")
for cid in h5p_ids - enrollment_ids:
    print(f"  - {cid}")

print(f"\nCourse IDs có cả ENROLLMENTS và H5P_SCORES:")
for cid in enrollment_ids & h5p_ids:
    print(f"  - {cid}")

cursor.close()
connection.close()
