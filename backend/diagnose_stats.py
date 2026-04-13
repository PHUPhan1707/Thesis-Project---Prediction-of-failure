# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('.')
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parents[0] / '.env')
from db import fetch_one, fetch_all

cid = 'course-v1:DHQG-HCM+ECON101+2026_S1'
print("=== mooc_grades for ECON101 ===")
agg = fetch_one("""SELECT COUNT(*) as total,
    SUM(grade_percentage IS NULL) as gp_null,
    SUM(grade_percentage = 0) as gp_zero,
    SUM(grade_percentage > 0) as gp_positive,
    ROUND(AVG(grade_percentage),2) as avg_gp,
    SUM(percent_grade IS NULL) as pg_null,
    SUM(percent_grade = 0) as pg_zero,
    SUM(percent_grade > 0) as pg_positive,
    ROUND(AVG(percent_grade),2) as avg_pg
FROM mooc_grades WHERE course_id = %s""", (cid,))
for k, v in agg.items():
    print(f"  {k}: {v}")

print("\n=== mooc_grades sample 5 rows ===")
for r in fetch_all("SELECT user_id, grade_percentage, percent_grade, letter_grade, is_passed FROM mooc_grades WHERE course_id = %s LIMIT 5", (cid,)):
    print(" ", r)
