import sys
sys.path.append('.')
from db import fetch_all

cid = 'course-v1:UEL+252BEE1038_04+2025_12'
rows = fetch_all(f"SELECT AVG(mooc_grade_percentage) as ag, AVG(mooc_completion_rate) as amc, AVG(overall_completion) as aoc, min(days_since_last_activity) as min_d, max(days_since_last_activity) as max_d, AVG(days_since_last_activity) as avg_d FROM student_features WHERE course_id='{cid}'")
print(rows)
