import os

class Settings:
    def __init__(self):
        self.mqtt_host = os.getenv("MQTT_HOST", "mqtt.bambulab.com")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "8883"))
        self.cert_path = os.getenv("CERT_PATH")

settings = Settings()
