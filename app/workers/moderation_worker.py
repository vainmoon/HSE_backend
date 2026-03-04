import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer

from clients.kafka import AsyncKafkaClient
from repositories.moderation_results import ModerationResultsRepository
from services.moderation import ModerationService
from services.model_manager import get_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:29092")
TOPIC = "moderation"


async def process_message(
    data: dict,
    model,
    moderation_repo: ModerationResultsRepository,
    moderation_service: ModerationService,
    kafka_client: AsyncKafkaClient,
):
    task_id = data["task_id"]
    item_id = data["item_id"]
    logger.info(f"Processing moderation task_id={task_id} for item_id={item_id}")

    try:
        pred, confidence = await moderation_service.moderate_item_by_id(model, item_id)
        await moderation_repo.update(
            task_id,
            status="completed",
            is_violation=bool(pred),
            probability=confidence,
            processed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        logger.info(f"task_id={task_id}: violation={bool(pred)}, confidence={confidence:.4f}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"task_id={task_id}: failed with error: {error_msg}")
        await moderation_repo.update(
            task_id,
            status="failed",
            error_message=error_msg,
            processed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        await kafka_client.send_to_dlq(data, error_msg)


async def run():
    model = get_model()
    moderation_repo = ModerationResultsRepository()
    moderation_service = ModerationService()

    kafka_client = AsyncKafkaClient(brokers=KAFKA_BROKERS)
    await kafka_client.start()

    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="moderation-worker",
    )

    await consumer.start()
    logger.info(f"Worker started, listening on topic '{TOPIC}'")

    try:
        async for message in consumer:
            try:
                await process_message(message.value, model, moderation_repo, moderation_service, kafka_client)
            except Exception as e:
                logger.error(f"Failed to process message: {e}")
    finally:
        await consumer.stop()
        await kafka_client.stop()


if __name__ == "__main__":
    asyncio.run(run())
