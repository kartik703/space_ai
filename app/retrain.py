from app.ingestion import update_dataset
from app.features import process_and_save
import json, os

def main():
    print("📥 Ingestion")
    update_dataset()
    print("🧱 Features")
    process_and_save()
    # Here you'd train and save real models; we just ensure meta exists
    os.makedirs("models", exist_ok=True)
    meta = {"best_model":"GRU","rmse_kp":0.3}
    with open("models/model_best.json","w") as f:
        json.dump(meta,f,indent=2)
    print("✅ Wrote models/model_best.json")
if __name__ == "__main__":
    main()
