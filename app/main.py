from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging

from routers.moderation import router as moderation_router
from services.model_manager import get_model
from errors import InferenceError, ModelUnavailableError, SellerNotFoundError, ItemNotFoundError
from clients.kafka import AsyncKafkaClient

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup")

    if not hasattr(app.state, "model") or app.state.model is None:
        app.state.model = get_model()

    app.state.kafka_client = AsyncKafkaClient()
    await app.state.kafka_client.start()

    yield
    logger.info("shutdown")
    await app.state.kafka_client.stop()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(InferenceError)
async def inference_error_handler(request, e):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Inference error: {e}"},
    )


@app.exception_handler(ModelUnavailableError)
async def model_unavailable_error_handler(request, e):
    return JSONResponse(
        status_code=503,
        content={"detail": f"Model is unavailable"},
    )

@app.exception_handler(SellerNotFoundError)
async def seller_not_found_error_handler(request, e):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Seller not found"},
    )

@app.exception_handler(ItemNotFoundError)
async def item_not_found_error_handler(request, e):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Item not found"},
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(moderation_router, prefix="/moderation")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
