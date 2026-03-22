import sys, traceback
sys.path.append('.')
from inference_service import InferenceService
from db import get_model_for_courses

try:
    cid = 'course-v1:UEL+252BEE1038_04+2025_12'
    m = get_model_for_courses([cid])
    print("Model info:", m)
    InferenceService(model_path=m['model_path'], features_csv=m['features_csv_path'])
    print("SUCCESS")
except Exception as e:
    with open('error_log.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
