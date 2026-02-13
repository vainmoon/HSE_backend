import logging
import mlflow
import os
import pickle
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)

USE_MLFLOW = os.getenv("USE_MLFLOW", "false").lower() == "true"
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "moderation-model")
MODEL_NAME = os.getenv("MODEL_NAME", "moderation-model")


def load_model_from_file(path="model.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_model_from_mlflow(model_name: str):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    client = MlflowClient()
    latest_versions = client.get_latest_versions(model_name)

    if not latest_versions:
        raise MlflowException(f"No registered versions found for model {model_name}")

    latest_version = max(int(v.version) for v in latest_versions)
    model_uri = f"models:/{model_name}/{latest_version}"
    return mlflow.sklearn.load_model(model_uri)


def get_model(model_path: str = "model.pkl"):
    if USE_MLFLOW:
        model = load_model_from_mlflow(MODEL_NAME)
        logger.info("Model loaded successfully from MLflow: %s", MODEL_NAME)
        return model

    model = load_model_from_file(model_path)
    logger.info("Model loaded successfully from file: %s", model_path)
    return model
