import json
from datetime import datetime
from aiokafka import AIOKafkaProducer

import logging
logger = logging.getLogger(__name__)

class AsyncKafkaClient:
    def __init__(self, brokers: str = "redpanda:29092"):
        self.brokers = brokers
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_moderation_request(self, item_id: int, task_id: int):
        message = {
            "task_id": task_id,
            "item_id": item_id,
            "timestamp": datetime.now().isoformat()
        }
        await self.producer.send_and_wait("moderation", value=message)
        logger.info(f"Sent moderation request: {message}")

    async def send_to_dlq(self, original_message: dict, error: str):
        retry_count = original_message.get("retry_count", 0) + 1
        dlq_message = {
            "original_message": original_message,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "retry_count": retry_count,
        }
        await self.producer.send_and_wait("moderation_dlq", value=dlq_message)
        logger.info(f"Sent to DLQ: task_id={original_message.get('task_id')}, retry_count={retry_count}")