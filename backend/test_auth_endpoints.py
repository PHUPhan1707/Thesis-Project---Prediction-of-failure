import os
import sys

sys.path.insert(0, r"d:\ProjectThesis\dropout_prediction")

from dotenv import load_dotenv
load_dotenv(r"d:\ProjectThesis\dropout_prediction\.env")

from backend.mooc_auth_service import MOOCAuthService

auth = MOOCAuthService()
success = auth.login()

if success:
    print(f"Login success! Session ID: {auth._session_id}")
    
    print("\n--- Testing Authenticated Endpoint ---")
    # Let's try to fetch an endpoint that definitely requires auth
    # According to fetch_mooc_h5p_data.py
    course_id = "course-v1:VNUHCM+001+2023" # A sample course ID, might be invalid
    
    try:
        url = f"https://mooc.vnuhcm.edu.vn/api/custom/v1/course-enrollments-attributes/{course_id}/"
        print(f"Fetching {url}")
        resp = auth.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
        
    print("\n--- Testing H5P Endpoint with Session ---")
    try:
        url = f"https://h5p.itp.vn/wp-json/mooc/v1/scores/1/{course_id}"
        print(f"Fetching {url}")
        resp = auth.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Login failed, cannot test.")
