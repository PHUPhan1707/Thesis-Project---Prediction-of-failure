import requests
import json

# Test without any authentication
course_id = "course-v1:VNUHCM+001+2023"

print("--- Testing MOOC Endpoint Without Auth ---")
url = f"https://mooc.vnuhcm.edu.vn/api/custom/v1/course-enrollments-attributes/{course_id}/"
resp = requests.get(url)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Data: {str(resp.json())[:200]}")
    
print("\n--- Testing H5P Endpoint Without Auth ---")
url = f"https://h5p.itp.vn/wp-json/mooc/v1/scores/1/{course_id}"
resp = requests.get(url)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Data: {str(resp.json())[:200]}")
