from pathlib import Path
import joblib

class MLPredictor:
    def __init__(self, model_dir):
        self.model_dir = Path(model_dir)
        self.category_model = self.model_dir / "category_model.joblib"
        self.priority_model = self.model_dir / "priority_model.joblib"
        self.version_file = self.model_dir / "model_version.txt"

    @property
    def ready(self):
        return self.category_model.exists() and self.priority_model.exists()

    def predict(self, message):
        if not self.ready:
            raise FileNotFoundError("ML model files are missing. Run dataset generation and model training first.")
        category_pipe = joblib.load(self.category_model)
        priority_pipe = joblib.load(self.priority_model)
        category = str(category_pipe.predict([message])[0])
        priority = str(priority_pipe.predict([message])[0])
        version = self.version_file.read_text(encoding="utf-8").strip() if self.version_file.exists() else "unknown"
        return {"category": category, "priority": priority, "model_version": version}
