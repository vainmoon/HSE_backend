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

    async def send_moderation_request(self, item_id: int):
        message = {
            "item_id": item_id,
            "timestamp": datetime.now().isoformat()
        }
        await self.producer.send_and_wait("moderation", value=message)
        logger.info(f"Sent moderation request: {message}")