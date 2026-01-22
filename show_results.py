"""
Quick script to show current prediction results
"""
import mysql.connector
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "port": 4000,
    "database": "dropout_prediction_db",
    "user": "dropout_user",
    "password": "dropout_pass_123"
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    course_id = "course-v1:DHQG-HCM+FM101+2025_S2"
    
    # Get prediction summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN fail_risk_score > 70 THEN 1 ELSE 0 END) as high_risk,
            SUM(CASE WHEN fail_risk_score BETWEEN 40 AND 70 THEN 1 ELSE 0 END) as medium_risk,
            SUM(CASE WHEN fail_risk_score < 40 THEN 1 ELSE 0 END) as low_risk,
            AVG(fail_risk_score) as avg_risk
        FROM raw_data
        WHERE course_id = %s AND fail_risk_score IS NOT NULL
    """, (course_id,))
    
    summary = cursor.fetchone()
    
    print("=" * 60)
    print("PREDICTION SUMMARY (Model V3 - Without Grade Leakage)")
    print("=" * 60)
    print(f"\nTotal students: {summary['total']}")
    print(f"Average fail risk: {summary['avg_risk']:.2f}%")
    print(f"\nRisk Distribution:")
    print(f"  HIGH (>70%):   {summary['high_risk']} ({summary['high_risk']/summary['total']*100:.1f}%)")
    print(f"  MEDIUM (40-70%): {summary['medium_risk']} ({summary['medium_risk']/summary['total']*100:.1f}%)")
    print(f"  LOW (<40%):    {summary['low_risk']} ({summary['low_risk']/summary['total']*100:.1f}%)")
    
    # Get top 10 at-risk students
    cursor.execute("""
        SELECT user_id, fail_risk_score, mooc_completion_rate, 
               days_since_last_activity
        FROM raw_data
        WHERE course_id = %s AND fail_risk_score IS NOT NULL
        ORDER BY fail_risk_score DESC
        LIMIT 10
    """, (course_id,))
    
    top_risk = cursor.fetchall()
    
    print(f"\nTop 10 At-Risk Students:")
    for student in top_risk:
        print(f"  User {student['user_id']}: {student['fail_risk_score']:.1f}% risk | "
              f"Completion: {student['mooc_completion_rate']:.1f}% | "
              f"Inactive: {student['days_since_last_activity']} days")
    
    # Check if Option 2 features exist
    cursor.execute("""
        SELECT COUNT(*) as with_percentile
        FROM raw_data
        WHERE course_id = %s AND performance_percentile IS NOT NULL
    """, (course_id,))
    
    option2_check = cursor.fetchone()
    
    print(f"\n" + "=" * 60)
    print("OPTION 2 STATUS:")
    print("=" * 60)
    if option2_check['with_percentile'] > 0:
        print(f"✅ Option 2 features available ({option2_check['with_percentile']} students)")
        
        # Show sample comparative features
        cursor.execute("""
            SELECT user_id, performance_percentile, 
                   is_below_course_average, relative_to_course_completion
            FROM raw_data
            WHERE course_id = %s AND performance_percentile IS NOT NULL
            LIMIT 5
        """, (course_id,))
        
        samples = cursor.fetchall()
        print("\nSample comparative features:")
        for s in samples:
            print(f"  User {s['user_id']}: Percentile={s['performance_percentile']}, "
                  f"Below avg={'Yes' if s['is_below_course_average'] else 'No'}, "
                  f"Relative completion={s['relative_to_course_completion']:.1f}%")
    else:
        print("❌ Option 2 features NOT available yet")
        print("   Run data collection to fetch course benchmarks")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
