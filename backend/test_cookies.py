import requests

# Set exactly what the service gets
cookies = {
    "sessionid": "1|pi2icftzkceol3ctrjud0ukahq2meqwz|eGXqdVhfGlRF|IjhkMGIzYzU3M2NhNmU5NjE3ZjVlMGJhNmQ4NWVlZDkwNDcxYWUwMTNmMDU0OWRiNGEzZDgwOGVjODAwZmE0NTQi:1w12W6:gXly4oE-a1L57pW8J2wY6EInE1t3T_CnbG-_HkZ4uKw",
    "edx-jwt-cookie-header-payload": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxNjk5OSwiZW1haWwiOiJwaGFuYW4ucGh1MTdAZ21haWwuY29tIiwidXNlcm5hbWUiOiJwaGExMTUiLCJhZG1pbmlzdHJhdG9yIjpmYWxzZSwiZXhwIjoxNzczNDE5MzYyfQ"
}

course_id = "course-v1:VNUHCM+001+2023"
url = f"https://mooc.vnuhcm.edu.vn/api/custom/v1/course-enrollments-attributes/{course_id}/"

print("--- Testing MOOC Endpoint With Only SessionID ---")
resp = requests.get(url, cookies={"sessionid": cookies["sessionid"]})
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Data: {str(resp.json())[:200]}")

print("\n--- Testing MOOC Endpoint With SessionID + JWT Cookie ---")
resp = requests.get(url, cookies=cookies)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Data: {str(resp.json())[:200]}")
