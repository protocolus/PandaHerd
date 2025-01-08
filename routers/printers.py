from typing import List
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from schemas import Printer, PrinterCreate, PrinterStatus, AMSSlot, AMS, PrintJob

router = APIRouter(prefix="/api/printers", tags=["printers"])

# Mock data
MOCK_PRINTERS = {
    "printer1": Printer(
        id="printer1",
        name="X1C-001",
        model="X1 Carbon",
        ip="192.168.1.101",
        status=PrinterStatus.PRINTING,
        ams=AMS(slots=[
            AMSSlot(color="#FF0000", name="Red PLA", remaining=85),
            AMSSlot(color="#00FF00", name="Green PLA", remaining=65),
            AMSSlot(color="#0000FF", name="Blue PLA", remaining=92),
            AMSSlot(color="#FFFFFF", name="White PLA", remaining=30),
        ]),
        current_job=PrintJob(
            id="job1",
            file_name="benchy.gcode",
            started_at=datetime.now() - timedelta(hours=1),
            estimated_time=12000,  # 3.33 hours in seconds
            progress=45,
            thumbnail_url="https://via.placeholder.com/150"
        )
    ),
    "printer2": Printer(
        id="printer2",
        name="P1P-001",
        model="P1P",
        ip="192.168.1.102",
        status=PrinterStatus.ONLINE,
        ams=None,
        current_job=None
    )
}

@router.get("/", response_model=List[Printer])
async def list_printers():
    """
    Get a list of all printers in the system.
    """
    return list(MOCK_PRINTERS.values())

@router.get("/{printer_id}", response_model=Printer)
async def get_printer(printer_id: str):
    """
    Get detailed information about a specific printer.
    """
    if printer_id not in MOCK_PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    return MOCK_PRINTERS[printer_id]

@router.post("/", response_model=Printer)
async def add_printer(printer: PrinterCreate):
    """
    Add a new printer to the system.
    """
    printer_id = f"printer{len(MOCK_PRINTERS) + 1}"
    new_printer = Printer(
        id=printer_id,
        name=printer.name,
        model=printer.model,
        ip=printer.ip,
        status=PrinterStatus.OFFLINE,
        ams=None,
        current_job=None
    )
    MOCK_PRINTERS[printer_id] = new_printer
    return new_printer

@router.delete("/{printer_id}")
async def remove_printer(printer_id: str):
    """
    Remove a printer from the system.
    """
    if printer_id not in MOCK_PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    del MOCK_PRINTERS[printer_id]
    return {"status": "success"}

@router.post("/{printer_id}/start")
async def start_printer(printer_id: str):
    """
    Start or resume printing on a specific printer.
    """
    if printer_id not in MOCK_PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    printer = MOCK_PRINTERS[printer_id]
    if printer.status == PrinterStatus.OFFLINE:
        raise HTTPException(status_code=400, detail="Printer is offline")
    if printer.status == PrinterStatus.PRINTING:
        raise HTTPException(status_code=400, detail="Printer is already printing")
    printer.status = PrinterStatus.PRINTING
    return {"status": "success"}

@router.post("/{printer_id}/pause")
async def pause_printer(printer_id: str):
    """
    Pause printing on a specific printer.
    """
    if printer_id not in MOCK_PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    printer = MOCK_PRINTERS[printer_id]
    if printer.status != PrinterStatus.PRINTING:
        raise HTTPException(status_code=400, detail="Printer is not printing")
    printer.status = PrinterStatus.PAUSED
    return {"status": "success"}

@router.post("/{printer_id}/stop")
async def stop_printer(printer_id: str):
    """
    Stop printing on a specific printer.
    """
    if printer_id not in MOCK_PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    printer = MOCK_PRINTERS[printer_id]
    if printer.status not in [PrinterStatus.PRINTING, PrinterStatus.PAUSED]:
        raise HTTPException(status_code=400, detail="Printer is not printing or paused")
    printer.status = PrinterStatus.ONLINE
    printer.current_job = None
    return {"status": "success"}
