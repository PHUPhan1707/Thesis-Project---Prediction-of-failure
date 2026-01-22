import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

course_id = "course-v1:DHQG-HCM+FM101+2025_S2"

# Get prediction summary
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN fail_risk_score > 70 THEN 1 ELSE 0 END) as high,
        SUM(CASE WHEN fail_risk_score BETWEEN 40 AND 70 THEN 1 ELSE 0 END) as med,
        SUM(CASE WHEN fail_risk_score < 40 THEN 1 ELSE 0 END) as low,
        AVG(fail_risk_score) as avg
    FROM raw_data
    WHERE course_id = %s AND fail_risk_score IS NOT NULL
""", (course_id,))

row = cursor.fetchone()

print("=" * 60)
print("CURRENT PREDICTION RESULTS (Model V3)")
print("=" * 60)
print(f"Total students: {row[0]}")
print(f"Average fail risk: {row[4]:.2f}%")
print(f"\nRisk Distribution:")
print(f"  HIGH (>70%):     {row[1]} ({row[1]/row[0]*100:.1f}%)")
print(f"  MEDIUM (40-70%): {row[2]} ({row[2]/row[0]*100:.1f}%)")
print(f"  LOW (<40%):      {row[3]} ({row[3]/row[0]*100:.1f}%)")

# Check Option 2 status
cursor.execute("""
    SELECT COUNT(*) FROM raw_data
    WHERE course_id = %s AND performance_percentile IS NOT NULL
""", (course_id,))

option2_count = cursor.fetchone()[0]

print(f"\n" + "=" * 60)
print("OPTION 2 STATUS:")
print("=" * 60)
if option2_count > 0:
    print(f"OK - Option 2 features available ({option2_count} students)")
else:
    print("NOT READY - Option 2 features NOT available yet")
    print("Need to run: python database/fetch_mooc_h5p_data.py --course-id ...")

cursor.close()
conn.close()
