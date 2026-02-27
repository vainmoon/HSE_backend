import asyncio
import json
import logging
import os
from typing import Optional

from aiokafka import AIOKafkaConsumer

from clients.kafka import KafkaClient
from repositories.items import ItemRepository
from repositories.sellers import SellerRepository
from repositories.moderation_results import ModerationResultRepository
from services.model_manager import get_model
from model import predict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
MODERATION_TOPIC = os.getenv('MODERATION_TOPIC', 'moderation')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY_SECONDS = int(os.getenv('RETRY_DELAY_SECONDS', '5'))


async def process_message(
    message: dict,
    model,
    item_repo: ItemRepository,
    seller_repo: SellerRepository,
    result_repo: ModerationResultRepository,
) -> None:
    """Core processing logic. Raises on any error."""
    task_id = message['task_id']
    item_id = message['item_id']

    item = await item_repo.get(item_id)
    seller = await seller_repo.get(item.seller_id)

    features = {
        "seller_id": seller.id,
        "is_verified_seller": seller.is_verified_seller,
        "item_id": item.id,
        "name": item.name,
        "description": item.description,
        "category": item.category,
        "images_qty": item.images_qty,
    }

    is_violation, probability = predict(model, features)

    await result_repo.update_completed(task_id, is_violation, probability)
    logger.info(
        "Task %s completed: is_violation=%s, probability=%s",
        task_id, is_violation, probability,
    )


async def handle_message(
    message: dict,
    model,
    kafka_client: KafkaClient,
    item_repo: ItemRepository,
    seller_repo: SellerRepository,
    result_repo: ModerationResultRepository,
) -> None:
    task_id = message['task_id']
    initial_retry_count = message.get('retry_count', 0)

    logger.info("Processing task_id=%s, item_id=%s", task_id, message['item_id'])

    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await process_message(message, model, item_repo, seller_repo, result_repo)
            return
        except Exception as e:
            last_error = e
            logger.warning(
                "Task %s attempt %s/%s failed: %s",
                task_id, attempt, MAX_RETRIES, e,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)

    # All retries exhausted
    final_retry_count = initial_retry_count + MAX_RETRIES
    error_message = str(last_error)

    logger.error("Task %s failed after %s attempts: %s", task_id, MAX_RETRIES, error_message)

    await result_repo.update_failed(task_id, error_message)
    await kafka_client.send_to_dlq(message, error_message, final_retry_count)
    logger.info("Task %s sent to DLQ (retry_count=%s)", task_id, final_retry_count)


async def run_worker() -> None:
    model = get_model()

    kafka_client = KafkaClient()
    await kafka_client.start()

    item_repo = ItemRepository()
    seller_repo = SellerRepository()
    result_repo = ModerationResultRepository()

    consumer = AIOKafkaConsumer(
        MODERATION_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        group_id='moderation-workers',
    )

    await consumer.start()
    logger.info("Worker started, consuming from topic '%s'", MODERATION_TOPIC)

    try:
        async for msg in consumer:
            await handle_message(
                msg.value, model, kafka_client,
                item_repo, seller_repo, result_repo,
            )
    finally:
        await consumer.stop()
        await kafka_client.stop()
        logger.info("Worker stopped")


if __name__ == '__main__':
    asyncio.run(run_worker())
