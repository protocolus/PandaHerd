from typing import Dict, Any, Optional
import json
import asyncio
from asyncio_mqtt import Client, MqttError
from .printer_state import update_printer_state

class MQTTClient:
    def __init__(self):
        self.printers: Dict[str, Dict[str, Any]] = {}
        self.client: Optional[Client] = None

    async def connect(self, broker: str, port: int = 1883):
        """Connect to the MQTT broker."""
        self.client = Client(broker, port)
        await self.client.connect()

    async def subscribe_to_printer(self, device_id: str):
        """Subscribe to a printer's MQTT topics."""
        if not self.client:
            raise RuntimeError("MQTT client not connected")
        
        # Subscribe to the printer's report topic
        topic = f"device/{device_id}/report"
        await self.client.subscribe(topic)

    async def process_messages(self):
        """Process incoming MQTT messages."""
        if not self.client:
            raise RuntimeError("MQTT client not connected")
        
        async with self.client.messages() as messages:
            async for message in messages:
                try:
                    # Parse the MQTT payload
                    payload = json.loads(message.payload)
                    
                    # Extract device ID from topic
                    device_id = message.topic.split('/')[1]
                    
                    # Update printer state if it contains AMS data
                    if "print" in payload and "ams" in payload["print"]:
                        ams_data = payload["print"]["ams"]
                        
                        # Extract AMS slot information
                        slots = []
                        for ams in ams_data.get("ams", []):
                            for slot in ams.get("slots", []):
                                slots.append({
                                    "color": slot.get("color", "#808080"),
                                    "remaining": slot.get("remain", 0),
                                    "material": slot.get("material", "Unknown"),
                                    "temperature": slot.get("temp", 0),
                                    "humidity": slot.get("humidity", 0)
                                })
                        
                        # Update printer state with new AMS data
                        if device_id in self.printers:
                            self.printers[device_id]["ams"] = {"slots": slots}
                            
                            # Notify the printer state service
                            await update_printer_state(device_id, self.printers[device_id])
                
                except json.JSONDecodeError:
                    print(f"Failed to parse MQTT message: {message.payload}")
                except Exception as e:
                    print(f"Error processing MQTT message: {e}")

    async def start(self, broker: str, device_ids: list[str]):
        """Start the MQTT client and subscribe to all printers."""
        try:
            await self.connect(broker)
            for device_id in device_ids:
                await self.subscribe_to_printer(device_id)
            await self.process_messages()
        except MqttError as e:
            print(f"MQTT Error: {e}")
            # Implement reconnection logic here
