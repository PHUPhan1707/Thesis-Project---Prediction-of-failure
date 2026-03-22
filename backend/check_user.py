import sys
import json
import io
sys.path.append('.')
from db import fetch_all

rows = fetch_all("SELECT * FROM student_features WHERE user_id=2389")

def default_serializer(obj):
    from decimal import Decimal
    from datetime import datetime
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

if rows:
    with io.open("user_2389_out.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, default=default_serializer, indent=2)
else:
    with io.open("user_2389_out.json", "w", encoding="utf-8") as f:
        f.write("[]")
