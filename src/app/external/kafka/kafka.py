from kafka import KafkaProducer
import json
import os

class KafkaProducerService:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def send_message(self, topic: str, key: str, value: dict):
        self.producer.send(topic, key=key.encode('utf-8'), value=value)
        self.producer.flush()
