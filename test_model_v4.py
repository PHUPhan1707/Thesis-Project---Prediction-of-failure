"""
Script kiểm tra Model V4 có hoàn chỉnh và hoạt động không
"""
import pickle
import pandas as pd
from catboost import CatBoostClassifier
from pathlib import Path

def test_model_v4():
    print("=" * 80)
    print("KIỂM TRA MODEL V4")
    print("=" * 80)
    
    model_dir = Path("models")
    
    # 1. Check files exist
    print("\n1. Kiểm tra các file cần thiết:")
    required_files = {
        "Model file (.cbm)": model_dir / "fm101_model_v4.cbm",
        "Metadata file": model_dir / "fm101_model_v4_metadata.pkl",
        "Metrics file": model_dir / "fm101_model_v4_metrics.pkl",
        "Feature importance": model_dir / "fm101_model_v4_feature_importance.csv"
    }
    
    all_exist = True
    for name, path in required_files.items():
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {name}: {path}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n❌ THIẾU FILE! Model v4 chưa hoàn chỉnh.")
        return False
    
    # 2. Load metadata
    print("\n2. Đọc metadata:")
    try:
        with open(model_dir / "fm101_model_v4_metadata.pkl", "rb") as f:
            metadata = pickle.load(f)
        
        print(f"   ✅ Trained at: {metadata.get('trained_at')}")
        print(f"   ✅ Number of features: {len(metadata.get('feature_names', []))}")
        print(f"   ✅ Categorical features: {len(metadata.get('categorical_features', []))}")
        print(f"   ✅ Model params: iterations={metadata['model_params'].get('iterations')}, "
              f"depth={metadata['model_params'].get('depth')}")
    except Exception as e:
        print(f"   ❌ Lỗi đọc metadata: {e}")
        return False
    
    # 3. Load metrics
    print("\n3. Đọc metrics:")
    try:
        with open(model_dir / "fm101_model_v4_metrics.pkl", "rb") as f:
            metrics = pickle.load(f)
        
        print(f"   ✅ AUC-ROC: {metrics.get('auc_roc', 0):.4f}")
        print(f"   ✅ Precision: {metrics.get('precision', 0):.4f}")
        print(f"   ✅ Recall: {metrics.get('recall', 0):.4f}")
        print(f"   ✅ F1-Score: {metrics.get('f1_score', 0):.4f}")
        print(f"   ✅ Accuracy: {metrics.get('classification_report', {}).get('accuracy', 0):.4f}")
        
        # Check if performance is good
        auc = metrics.get('auc_roc', 0)
        f1 = metrics.get('f1_score', 0)
        
        if auc >= 0.85 and f1 >= 0.75:
            print(f"\n   🎉 PERFORMANCE TUYỆT VỜI! (AUC={auc:.4f}, F1={f1:.4f})")
        elif auc >= 0.70 and f1 >= 0.60:
            print(f"\n   👍 Performance tốt (AUC={auc:.4f}, F1={f1:.4f})")
        else:
            print(f"\n   ⚠️ Performance cần cải thiện (AUC={auc:.4f}, F1={f1:.4f})")
            
    except Exception as e:
        print(f"   ❌ Lỗi đọc metrics: {e}")
        return False
    
    # 4. Load model
    print("\n4. Load CatBoost model:")
    try:
        model = CatBoostClassifier()
        model.load_model(str(model_dir / "fm101_model_v4.cbm"))
        print(f"   ✅ Model loaded successfully!")
        print(f"   ✅ Tree count: {model.tree_count_}")
        print(f"   ✅ Feature names: {len(model.feature_names_)} features")
    except Exception as e:
        print(f"   ❌ Lỗi load model: {e}")
        return False
    
    # 5. Test prediction with dummy data
    print("\n5. Test prediction với dummy data:")
    try:
        # Create dummy data with all required features
        feature_names = metadata['feature_names']
        categorical_features = metadata['categorical_features']
        
        # Create a sample row
        sample_data = {}
        for feat in feature_names:
            if feat in categorical_features:
                sample_data[feat] = 'unknown'
            else:
                sample_data[feat] = 0.5
        
        # Convert to DataFrame
        df_sample = pd.DataFrame([sample_data])
        
        # Make prediction
        pred_proba = model.predict_proba(df_sample)
        pred_class = model.predict(df_sample)
        
        print(f"   ✅ Prediction successful!")
        print(f"   ✅ Predicted class: {pred_class[0]}")
        print(f"   ✅ Predicted probability: [Not Fail: {pred_proba[0][0]:.4f}, Fail: {pred_proba[0][1]:.4f}]")
        
    except Exception as e:
        print(f"   ❌ Lỗi test prediction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Check feature importance
    print("\n6. Kiểm tra feature importance:")
    try:
        df_importance = pd.read_csv(model_dir / "fm101_model_v4_feature_importance.csv")
        print(f"   ✅ Feature importance loaded: {len(df_importance)} features")
        print("\n   Top 5 features quan trọng nhất:")
        for i, row in df_importance.head(5).iterrows():
            print(f"      {i+1}. {row['feature']}: {row['importance']:.2f}")
    except Exception as e:
        print(f"   ❌ Lỗi đọc feature importance: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("KẾT LUẬN")
    print("=" * 80)
    print("✅ MODEL V4 ĐÃ HOÀN CHỈNH VÀ SẴN SÀNG SỬ DỤNG!")
    print(f"✅ Performance: AUC={metrics.get('auc_roc', 0):.4f}, F1={metrics.get('f1_score', 0):.4f}")
    print(f"✅ Trained on: {metadata.get('trained_at')}")
    print(f"✅ Total features: {len(metadata.get('feature_names', []))}")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_model_v4()
    exit(0 if success else 1)

