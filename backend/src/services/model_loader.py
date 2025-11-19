import tensorflow as tf
from pathlib import Path
from src.utils import load_obj
from src.components.data_transformation import DataTransformation


MODEL_CACHE = {}


class ModelBundle:
    def __init__(self, symbol):
        base = Path("artifacts/models") / symbol


        self.direction = tf.keras.models.load_model(base / f"{symbol}_direction.keras")
        self.return_model = tf.keras.models.load_model(base / f"{symbol}_return.keras")
        self.ind_scaler = load_obj(base / "ind_scaler.pkl")
        self.target_scaler = load_obj(base / "target_scaler.pkl")
        self.transformer = DataTransformation()


def get_model(symbol):
    if symbol not in MODEL_CACHE:
        MODEL_CACHE[symbol] = ModelBundle(symbol)
    return MODEL_CACHE[symbol]