import logging
from model import load_model, train_model, save_model

logger = logging.getLogger(__name__)


def load_or_train_model(model_path: str = "model.pkl"):
    try:
        model = load_model(model_path)
        logger.info("Model loaded successfully from file: %s", model_path)
        return model
    except FileNotFoundError:
        logger.info("Model not found at %s, training new model...", model_path)
        model = train_model()
        save_model(model, model_path)
        logger.info("Model trained and saved successfully to: %s", model_path)
        return model
