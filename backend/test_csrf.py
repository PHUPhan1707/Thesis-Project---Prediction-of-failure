import requests
import json

cookies = {
    "sessionid": "1|pi2icftzkceol3ctrjud0ukahq2meqwz|eGXqdVhfGlRF|IjhkMGIzYzU3M2NhNmU5NjE3ZjVlMGJhNmQ4NWVlZDkwNDcxYWUwMTNmMDU0OWRiNGEzZDgwOGVjODAwZmE0NTQi:1w12W6:gXly4oE-a1L57pW8J2wY6EInE1t3T_CnbG-_HkZ4uKw",
    "csrftoken": "0t10yHjGqP5Q6yGIf8u5L4zO0F5y1tSFT31xXqfF1Q5voilrg5aUEJmMzNiZWJmYTlh"
}

headers = {
    "X-CSRFToken": cookies["csrftoken"],
    "Referer": "https://mooc.vnuhcm.edu.vn/",
    "Origin": "https://mooc.vnuhcm.edu.vn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

course_id = "course-v1:VNUHCM+001+2023"
url = f"https://mooc.vnuhcm.edu.vn/api/custom/v1/course-enrollments-attributes/{course_id}/"

print("--- Testing MOOC Endpoint With Full Headers & Cookies ---")
resp = requests.get(url, headers=headers, cookies=cookies)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Data: {str(resp.json())[:200]}")
