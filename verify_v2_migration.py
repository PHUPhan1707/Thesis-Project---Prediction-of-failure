"""
Verification script cho migration V2
Kiểm tra xem migration có thành công không
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.db import fetch_all, fetch_one

print("="*80)
print("VERIFICATION: Schema V2 Migration")
print("="*80)

# 1. Check tables exist
print("\n1. Checking tables exist...")
tables_to_check = [
    'student_features',
    'predictions', 
    'training_data',
    'model_registry',
    'course_model_mapping'
]

for table in tables_to_check:
    result = fetch_one(f"SHOW TABLES LIKE '{table}'")
    if result:
        print(f"   ✅ {table}")
    else:
        print(f"   ❌ {table} - NOT FOUND!")

# 2. Check record counts
print("\n2. Record counts:")
counts = {}
for table in ['raw_data', 'student_features', 'predictions', 'training_data']:
    try:
        result = fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
        counts[table] = result['cnt'] if result else 0
        print(f"   - {table:20s}: {counts[table]:>6} records")
    except Exception as e:
        print(f"   - {table:20s}: ERROR - {e}")
        counts[table] = 0

# 3. Check courses
print("\n3. Courses in student_features:")
courses = fetch_all("SELECT DISTINCT course_id FROM student_features")
for c in courses:
    course_id = c['course_id']
    result = fetch_one("SELECT COUNT(*) as cnt FROM student_features WHERE course_id = %s", (course_id,))
    cnt = result['cnt'] if result else 0
    print(f"   - {course_id}: {cnt} students")

# 4. Check predictions
print("\n4. Predictions summary:")
pred_stats = fetch_all("""
    SELECT 
        model_name,
        COUNT(*) as total_preds,
        AVG(fail_risk_score) as avg_risk,
        MIN(predicted_at) as first_pred,
        MAX(predicted_at) as last_pred
    FROM predictions
    GROUP BY model_name
""")

for p in pred_stats:
    print(f"   - Model: {p['model_name']}")
    print(f"     Total: {p['total_preds']} predictions")
    print(f"     Avg risk: {p['avg_risk']:.2f}%")
    print(f"     First: {p['first_pred']}")
    print(f"     Last: {p['last_pred']}")

# 5. Check model registry
print("\n5. Model Registry:")
models = fetch_all("SELECT model_name, model_version, is_active, is_default FROM model_registry")
for m in models:
    status = "✅ ACTIVE" if m['is_active'] else "❌ INACTIVE"
    default = " (DEFAULT)" if m['is_default'] else ""
    print(f"   - {m['model_name']} v{m['model_version']}: {status}{default}")

# 6. Check course mappings
print("\n6. Course Model Mappings:")
mappings = fetch_all("""
    SELECT course_id, model_name, auto_predict, is_active 
    FROM course_model_mapping
""")
for mapping in mappings:
    status = "✅" if mapping['is_active'] else "❌"
    auto = "🤖 AUTO" if mapping['auto_predict'] else "👤 MANUAL"
    print(f"   {status} {mapping['course_id']}")
    print(f"      → Model: {mapping['model_name']} ({auto})")

# 7. Validation checks
print("\n7. Validation:")
issues = []

# Check 1: student_features >= raw_data
if counts['student_features'] < counts['raw_data']:
    issues.append(f"student_features ({counts['student_features']}) < raw_data ({counts['raw_data']})")
else:
    print(f"   ✅ student_features count OK ({counts['student_features']} >= {counts['raw_data']})")

# Check 2: predictions should have data
if counts['predictions'] == 0:
    issues.append("predictions table is empty!")
else:
    print(f"   ✅ predictions has {counts['predictions']} records")

# Check 3: model registry should have at least 1 model
model_count = len(models)
if model_count == 0:
    issues.append("model_registry is empty!")
else:
    print(f"   ✅ model_registry has {model_count} model(s)")

# Check 4: course mappings should exist
mapping_count = len(mappings)
if mapping_count == 0:
    print(f"   ⚠️  No course mappings (will use default model)")
else:
    print(f"   ✅ {mapping_count} course mapping(s) configured")

# 8. Test queries (simulate API)
print("\n8. Test API-like queries:")

# Test: Get students with predictions
test_course = courses[0]['course_id'] if courses else None
if test_course:
    print(f"\n   Testing course: {test_course}")
    
    students = fetch_all(f"""
        SELECT 
            f.user_id,
            f.mooc_grade_percentage,
            COALESCE(p.fail_risk_score, 50) as fail_risk_score,
            p.model_name
        FROM student_features f
        LEFT JOIN predictions p ON f.user_id = p.user_id 
            AND f.course_id = p.course_id 
            AND p.is_latest = TRUE
        WHERE f.course_id = %s
        LIMIT 5
    """, (test_course,))
    
    print(f"   Sample students (first 5):")
    for s in students:
        pred_source = f"[{s['model_name']}]" if s['model_name'] else "[placeholder]"
        print(f"     - User {s['user_id']}: Risk={s['fail_risk_score']:.1f}% {pred_source}")

# 9. Summary
print("\n" + "="*80)
if issues:
    print("❌ MIGRATION HAS ISSUES:")
    for issue in issues:
        print(f"   - {issue}")
else:
    print("✅ MIGRATION SUCCESSFUL!")
    print("\n📊 Summary:")
    print(f"   - student_features:  {counts['student_features']} records")
    print(f"   - predictions:       {counts['predictions']} records")
    print(f"   - training_data:     {counts['training_data']} records")
    print(f"   - model_registry:    {model_count} model(s)")
    print(f"   - course_mappings:   {mapping_count} mapping(s)")
print("="*80)
