import requests
import os
import sys

sys.path.insert(0, r"d:\ProjectThesis\dropout_prediction")
from dotenv import load_dotenv
load_dotenv(r"d:\ProjectThesis\dropout_prediction\.env")

email = os.getenv("MOOC_EMAIL")
password = os.getenv("MOOC_PASSWORD")
base_url = "https://mooc.vnuhcm.edu.vn"

# Let's see if we can get a JWT token
print("--- Attempting to get JWT Token ---")
jwt_url = f"{base_url}/api/user/v1/jwt/cookies/"
session = requests.Session()

# Login first
session.headers.update({
    "User-Agent": "DropoutPrediction/2.0",
    "Referer": f"{base_url}/login",
    "Origin": base_url,
})

csrf_resp = session.get(f"{base_url}/csrf/api/v1/token")
csrf_token = csrf_resp.json().get("csrfToken", "")

session.headers["X-CSRFToken"] = csrf_token
session.headers["Content-Type"] = "application/x-www-form-urlencoded"

login_resp = session.post(
    f"{base_url}/api/user/v1/account/login_session/",
    data={"email": email, "password": password}
)
print(f"Login Status: {login_resp.status_code}")

if login_resp.status_code == 200:
    for cookie in session.cookies:
        if "jwt" in cookie.name.lower():
            print(f"Found JWT Cookie: {cookie.name} = {cookie.value[:20]}...")

    # Let's try the endpoint with the authenticated session directly
    course_id = "course-v1:VNUHCM+001+2023"
    url = f"{base_url}/api/custom/v1/course-enrollments-attributes/{course_id}/"
    
    print("\n--- Trying API with the raw session ---")
    api_resp = session.get(url)
    print(f"Status: {api_resp.status_code}")
    if api_resp.status_code == 200:
        print(f"Data: {str(api_resp.json())[:200]}")
    else:
        print(api_resp.text[:300])

