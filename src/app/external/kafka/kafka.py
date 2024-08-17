import json
import os

from kafka import KafkaProducer


class KafkaProducerService:
    """Сервис для отправки сообщений в Kafka."""

    def __init__(self):
        """Инициализирует KafkaProducerService с Kafka producer."""
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_serializer=lambda message: json.dumps(message).encode('utf-8'),
        )

    def send_message(self, topic: str, key: str, message_data: dict):
        """Отправляет сообщение в указанный Kafka топик."""
        self.producer.send(topic, key=key.encode('utf-8'), value=message_data)
        self.producer.flush()
