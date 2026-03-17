import os
import sys

sys.path.insert(0, r"d:\ProjectThesis\dropout_prediction")

from dotenv import load_dotenv
load_dotenv(r"d:\ProjectThesis\dropout_prediction\.env")

from backend.mooc_auth_service import MOOCAuthService

print(f"MOOC_EMAIL: {os.getenv('MOOC_EMAIL')}")
print(f"MOOC_PASSWORD length: {len(os.getenv('MOOC_PASSWORD', ''))}")

auth = MOOCAuthService()
print(f"Is configured: {auth.is_configured}")

print("Attempting login...")
success = auth.login()

print(f"\nLogin success: {success}")
print(f"Status: {auth.status}")
if hasattr(auth, '_session_id'):
    print(f"Session ID: {auth._session_id}")
