import json
import os
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
MODERATION_TOPIC = os.getenv('MODERATION_TOPIC', 'moderation')
DLQ_TOPIC = os.getenv('DLQ_TOPIC', 'moderation_dlq')


class KafkaClient:
    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
        )
        await self._producer.start()

    async def stop(self):
        if self._producer:
            await self._producer.stop()

    async def send_moderation_request(self, task_id: int, item_id: int) -> None:
        message = {
            'task_id': task_id,
            'item_id': item_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'retry_count': 0,
        }
        await self._producer.send(
            MODERATION_TOPIC,
            value=json.dumps(message).encode('utf-8'),
        )

    async def send_to_dlq(self, original_message: dict, error: str, retry_count: int) -> None:
        message = {
            'original_message': original_message,
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'retry_count': retry_count,
        }
        await self._producer.send(
            DLQ_TOPIC,
            value=json.dumps(message).encode('utf-8'),
        )
