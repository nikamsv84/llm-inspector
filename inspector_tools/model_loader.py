import joblib
from pathlib import Path



class ModelLoader:
    def __init__(self, models_dir: Path):
        self.body_model_path = models_dir / "body_model.pkl"
        self.header_model_path = models_dir / "header_model.pkl"
        self.body_model = None  #already not loaded
        self.header_model = None #already not loaded too.


    def load_models(self):
        try:
            self.body_model = joblib.load(self.body_model_path)
        except FileNotFoundError:
            print(f"body model not found in {self.body_model_path}")


        try:
            self.header_model = joblib.load(self.header_model_path)
        except FileNotFoundError:
            print(f"header model not found {self.header_model_path}")
