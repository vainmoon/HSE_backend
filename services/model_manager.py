import logging
import mlflow
from mlflow.sklearn import log_model
import os
import pickle
from model import train_model
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)

use_mlflow = os.getenv('USE_MLFLOW', 'false').lower() == 'true'
if use_mlflow:
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("moderation-model")

def save_model(model, path="model.pkl") -> None:
    with open(path, "wb") as f:
        pickle.dump(model, f)


def load_model_from_file(path="model.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

def load_model_from_mlflow(model_name: str):
    client = MlflowClient()
    latest_versions = client.get_latest_versions(model_name)
    if not latest_versions:
        raise MlflowException(f"No registered versions found for model {model_name}")
    latest_version = max([int(v.version) for v in latest_versions])
    model_uri = f"models:/{model_name}/{latest_version}"
    return mlflow.sklearn.load_model(model_uri)

def load_or_train_model(model_path: str = "model.pkl"):
    try:   
        if use_mlflow:
            model = load_model_from_mlflow("moderation-model")
            logger.info("Model loaded successfully from MLflow: %s", "moderation-model")
        else:
            model = load_model_from_file(model_path)
            logger.info("Model loaded successfully from file: %s", model_path)
        return model

    except (FileNotFoundError, MlflowException):
        logger.info("Model not found at %s, training new model...", model_path)
        if use_mlflow:
            with mlflow.start_run():
                model = train_model()
                log_model(model, "model", registered_model_name="moderation-model")
                logger.info("Model trained and logged to MLflow successfully: %s", "moderation-model")
        else:
            model = train_model()
            save_model(model, model_path)
            logger.info("Model trained and saved successfully to: %s", model_path)
        return model
