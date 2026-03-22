import sys
import logging
logging.basicConfig(level=logging.INFO)

from inference_service import InferenceService
from db import get_model_for_courses

cid = "course-v1:UEL+252BEE1038_04+2025_12"
print(f"Testing prediction for course {cid}")

model = get_model_for_courses([cid])
print(f"Model Info: {model}")

if model:
    service = InferenceService(
        model_path=model.get("model_path"),
        features_csv=model.get("features_csv_path"),
    )
    result_df = service.predict_course(cid, save_db=True)
    if result_df is not None:
        print(f"Predicted shape: {result_df.shape}")
        if result_df.empty:
            print("Why empty? Let's check raw_data fetcher:")
            raw = service._fetcher.fetch_course(cid)
            print(f"raw_df shape: {raw.shape if raw is not None else 'None'}")
            feat = service._preparator.engineer_features(raw.copy()) if raw is not None else None
            print(f"feat_df shape: {feat.shape if feat is not None else 'None'}")
    else:
        print("Result is None")
