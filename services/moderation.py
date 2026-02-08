from model import predict
from errors import ModelUnavailableError, InferenceError


class ModerationService:
    def moderate_item(self, model, moderate_item: dict):
        if model is None:
            raise ModelUnavailableError

        try:
            pred, confidence = predict(model, moderate_item)
            return pred, confidence

        except Exception as e:
            raise InferenceError(e)
