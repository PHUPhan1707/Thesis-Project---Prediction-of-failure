import os
import sys
import json
import traceback

sys.path.insert(0, r"d:\ProjectThesis\dropout_prediction")
from dotenv import load_dotenv
load_dotenv(r"d:\ProjectThesis\dropout_prediction\.env")

from backend.pipeline_service import PipelineService
from backend.mooc_auth_service import get_mooc_auth

try:
    auth = get_mooc_auth()
    success = auth.login()
    if not success:
        print("Login failed, aborting test.")
        exit(1)
        
    print(f"Login success! Session ID: {auth._session_id}")

    # Mock courses
    courses = [{"id": "course-v1:VNUHCM+001+2023", "display_name": "Test Course"}]

    pipeline = PipelineService()
    print("Running pipeline _step2_fetch...")
    
    # Test step 2 directly
    pipeline._step2_fetch(courses, session_id="")

    print("\n--- Pipeline Logs ---")
    while not pipeline._queue.empty():
        event = pipeline._queue.get()
        print(f"[{event.event_type}] {json.dumps(event.data, ensure_ascii=False)}")
except Exception as e:
    print(f"Exception out: {e}")
    traceback.print_exc()
