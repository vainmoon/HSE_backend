import numpy as np
from sklearn.linear_model import LogisticRegression
import pickle


def train_model():
    """Обучает простую модель на синтетических данных."""
    np.random.seed(42)
    # Признаки: [is_verified_seller, images_qty, description_length, category]
    X = np.random.rand(1000, 4)
    # Целевая переменная: 1 = нарушение, 0 = нет нарушения
    y = (X[:, 0] < 0.3) & (X[:, 1] < 0.2)
    y = y.astype(int)

    model = LogisticRegression()
    model.fit(X, y)
    return model


def save_model(model, path="model.pkl") -> None:
    with open(path, "wb") as f:
        pickle.dump(model, f)


def load_model(path="model.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)


def preprocess(row: dict) -> list:
    preprocess_row = {}
    preprocess_row["is_verified_seller"] = float(row["is_verified_seller"])
    preprocess_row["images_qty"] = row["images_qty"] / 10
    preprocess_row["len_description"] = len(row["description"]) / 1000
    preprocess_row["category"] = row["category"] / 100
    return list(preprocess_row.values())


def predict(model, row: dict) -> tuple[int, float]:
    preprocess_row = [preprocess(row)]
    pred = int(model.predict(preprocess_row)[0])
    proba = model.predict_proba(preprocess_row)[0]
    confidence = float(max(proba))
    return pred, confidence
