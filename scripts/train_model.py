import argparse
import logging
import os
import pickle

import mlflow
from mlflow.sklearn import log_model

from app.model import train_model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def save_model(model, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)


def train_and_save_model(
    save_path: str = "model.pkl",
    model_name: str = "moderation-model",
    use_mlflow: bool = False,
):
    model = train_model()
    logger.info("Model trained successfully")

    save_model(model, save_path)
    logger.info("Model saved successfully to: %s", save_path)

    if use_mlflow:
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        mlflow.set_experiment("moderation-model")

        with mlflow.start_run():
            log_model(model, "model", registered_model_name=model_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="model.pkl")
    parser.add_argument("--name", type=str, default="moderation-model")
    parser.add_argument("--use-mlflow", action="store_true")

    args = parser.parse_args()

    train_and_save_model(
        save_path=args.path,
        model_name=args.name,
        use_mlflow=args.use_mlflow,
    )


if __name__ == "__main__":
    main()
