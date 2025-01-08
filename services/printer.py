import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pandaherd.models.printer import Printer
from pandaherd.services.mqtt import mqtt_client

logger = logging.getLogger(__name__)

class PrinterService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_printers(self) -> List[Printer]:
        result = await self.session.execute(select(Printer))
        return result.scalars().all()
    
    async def get_printer(self, printer_id: int) -> Optional[Printer]:
        result = await self.session.execute(
            select(Printer).where(Printer.id == printer_id)
        )
        return result.scalar_one_or_none()
    
    async def add_printer(
        self, name: str, serial: str, model: str, ip_address: Optional[str] = None
    ) -> Printer:
        printer = Printer(
            name=name,
            serial=serial,
            model=model,
            ip_address=ip_address,
        )
        self.session.add(printer)
        await self.session.commit()
        
        # Subscribe to printer's MQTT topic
        mqtt_client.subscribe(serial)
        
        return printer
    
    async def update_printer_status(self, printer_id: int, status: str) -> Optional[Printer]:
        printer = await self.get_printer(printer_id)
        if printer:
            printer.status = status
            await self.session.commit()
        return printer
    
    async def remove_printer(self, printer_id: int) -> bool:
        printer = await self.get_printer(printer_id)
        if printer:
            # Unsubscribe from printer's MQTT topic
            mqtt_client.unsubscribe(printer.serial)
            
            await self.session.delete(printer)
            await self.session.commit()
            return True
        return False
