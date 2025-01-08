from typing import List
from fastapi import APIRouter, HTTPException
from datetime import datetime
from schemas import PrintJob, PrintJobCreate, PrinterStatus
from routers.printers import MOCK_PRINTERS

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Mock data
MOCK_JOBS = {
    "job1": PrintJob(
        id="job1",
        file_name="benchy.gcode",
        started_at=datetime.now(),
        estimated_time=12000,  # 3.33 hours in seconds
        progress=45,
        thumbnail_url="https://via.placeholder.com/150"
    )
}

@router.get("/", response_model=List[PrintJob])
async def list_jobs():
    """
    Get a list of all print jobs in the system.
    """
    return list(MOCK_JOBS.values())

@router.get("/{job_id}", response_model=PrintJob)
async def get_job(job_id: str):
    """
    Get detailed information about a specific print job.
    """
    if job_id not in MOCK_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return MOCK_JOBS[job_id]

@router.post("/", response_model=PrintJob)
async def create_job(job: PrintJobCreate):
    """
    Create a new print job and assign it to a printer.
    """
    if job.printer_id not in MOCK_PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    printer = MOCK_PRINTERS[job.printer_id]
    if printer.status != PrinterStatus.ONLINE:
        raise HTTPException(status_code=400, detail="Printer is not available")
    
    job_id = f"job{len(MOCK_JOBS) + 1}"
    new_job = PrintJob(
        id=job_id,
        file_name=job.file_name,
        started_at=datetime.now(),
        estimated_time=7200,  # Mock 2 hour print time
        progress=0,
        thumbnail_url=None
    )
    
    MOCK_JOBS[job_id] = new_job
    printer.current_job = new_job
    printer.status = PrinterStatus.PRINTING
    
    return new_job

@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a print job and stop the associated printer.
    """
    if job_id not in MOCK_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Find printer running this job
    printer = next(
        (p for p in MOCK_PRINTERS.values() if p.current_job and p.current_job.id == job_id),
        None
    )
    
    if printer:
        printer.status = PrinterStatus.ONLINE
        printer.current_job = None
    
    del MOCK_JOBS[job_id]
    return {"status": "success"}
