import sys
import logging
from pprint import pprint
# Setup logging
logging.basicConfig(level=logging.INFO)

from db import discover_course_groups, get_model_for_courses, fetch_all

groups = discover_course_groups()
print(f"Groups: {groups}")

for base_name, course_ids in groups.items():
    if "Kinh tế vĩ mô" in base_name:
        print(f"\n--- Checking '{base_name}' ---")
        model = get_model_for_courses(course_ids)
        print(f"Model for these courses: {model}")
        
        for cid in course_ids:
            raw = fetch_all("SELECT COUNT(*) as c FROM raw_data WHERE course_id=%s", (cid,))
            feat = fetch_all("SELECT COUNT(*) as c FROM student_features WHERE course_id=%s", (cid,))
            pred = fetch_all("SELECT COUNT(*) as c FROM predictions WHERE course_id=%s", (cid,))
            enroll = fetch_all("SELECT COUNT(*) as c FROM enrollments WHERE course_id=%s", (cid,))
            print(f"Course {cid}: enrollments={enroll[0]['c']}, raw_data={raw[0]['c']}, student_features={feat[0]['c']}, predictions={pred[0]['c']}")

print("\nRecent Training History:")
hist = fetch_all("SELECT base_name, model_name, action, status, completed_at FROM training_history ORDER BY completed_at DESC LIMIT 5")
pprint(hist)
