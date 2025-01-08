from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class PrinterStatus(str, Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
    PRINTING = "Printing"
    PAUSED = "Paused"
    ERROR = "Error"

class AMSSlot(BaseModel):
    color: str = Field(..., description="Hex color code of the filament")
    name: str = Field(..., description="Name of the filament")
    remaining: int = Field(..., description="Percentage of filament remaining", ge=0, le=100)

class AMS(BaseModel):
    slots: List[AMSSlot] = Field(..., description="List of AMS slots")

class PrintJob(BaseModel):
    id: str = Field(..., description="Unique ID of the print job")
    file_name: str = Field(..., description="Name of the file being printed")
    started_at: datetime = Field(..., description="When the print started")
    estimated_time: int = Field(..., description="Estimated print time in seconds")
    progress: int = Field(..., description="Print progress percentage", ge=0, le=100)
    thumbnail_url: Optional[str] = Field(None, description="URL to print preview thumbnail")

class Printer(BaseModel):
    id: str = Field(..., description="Unique ID of the printer")
    name: str = Field(..., description="Display name of the printer")
    model: str = Field(..., description="Printer model (X1C, P1P, etc)")
    ip: str = Field(..., description="IP address of the printer")
    status: PrinterStatus = Field(..., description="Current printer status")
    ams: Optional[AMS] = Field(None, description="AMS configuration if available")
    current_job: Optional[PrintJob] = Field(None, description="Currently running print job")

class PrinterCreate(BaseModel):
    name: str = Field(..., description="Display name of the printer")
    model: str = Field(..., description="Printer model (X1C, P1P, etc)")
    ip: str = Field(..., description="IP address of the printer")

class PrintJobCreate(BaseModel):
    file_name: str = Field(..., description="Name of the file to print")
    printer_id: str = Field(..., description="ID of the printer to use")
