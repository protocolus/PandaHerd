import json
import logging
from typing import Optional

import paho.mqtt.client as mqtt

from pandaherd.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class BambuMQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        if settings.CERT_PATH:
            self.client.tls_set(settings.CERT_PATH)
    
    def connect(self, username: Optional[str] = None, password: Optional[str] = None):
        if username and password:
            self.client.username_pw_set(username, password)
        
        try:
            self.client.connect(settings.MQTT_HOST, settings.MQTT_PORT)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"Received message on topic {msg.topic}: {payload}")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode message on topic {msg.topic}")
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")
    
    def subscribe(self, serial: str):
        topic = f"device/{serial}/report"
        self.client.subscribe(topic)
        logger.info(f"Subscribed to topic: {topic}")
    
    def unsubscribe(self, serial: str):
        topic = f"device/{serial}/report"
        self.client.unsubscribe(topic)
        logger.info(f"Unsubscribed from topic: {topic}")

mqtt_client = BambuMQTTClient()
