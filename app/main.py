import os

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from routers.moderation import router as moderation_router
from routers.auth import router as auth_router
from services.model_manager import get_model
from errors import *
from clients.kafka import AsyncKafkaClient

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    integrations=[StarletteIntegration(), FastApiIntegration()],
    traces_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "development"),
)


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
Instrumentator().instrument(
    app,
    latency_lowr_buckets=[0.001, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
).expose(app)

@app.exception_handler(InferenceError)
async def inference_error_handler(request, e):
    sentry_sdk.capture_exception(e)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Inference error: {e}"},
    )


@app.exception_handler(ModelUnavailableError)
async def model_unavailable_error_handler(request, e):
    sentry_sdk.capture_exception(e)
    return JSONResponse(
        status_code=503,
        content={"detail": f"Model is unavailable"},
    )

@app.exception_handler(SellerNotFoundError)
async def seller_not_found_error_handler(request, e):
    sentry_sdk.capture_exception(e)
    return JSONResponse(
        status_code=404,
        content={"detail": f"Seller not found"},
    )

@app.exception_handler(AccountNotFoundError)
async def account_not_found_error_handler(request, e):
    sentry_sdk.capture_exception(e)
    return JSONResponse(
        status_code=404,
        content={"detail": f"Account not found"},
    )

@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_error_handler(request, e):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid login or password"},
    )

@app.exception_handler(AccountBlockedError)
async def account_blocked_error_handler(request, e):
    return JSONResponse(
        status_code=403,
        content={"detail": "Account is blocked"},
    )

@app.exception_handler(ItemNotFoundError)
async def item_not_found_error_handler(request, e):
    sentry_sdk.capture_exception(e)
    return JSONResponse(
        status_code=404,
        content={"detail": f"Item not found"},
    )

@app.exception_handler(ModerationResultNotFoundError)
async def moderation_result_not_found_error_handler(request, e):
    sentry_sdk.capture_exception(e)
    return JSONResponse(
        status_code=404,
        content={"detail": f"Moderation result not found"},
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(moderation_router, prefix="/moderation")
app.include_router(auth_router, prefix="/auth")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
