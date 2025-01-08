from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from datetime import datetime

router = APIRouter(
    prefix="/api/library",
    tags=["library"],
    responses={404: {"description": "Not found"}},
)

# Mock data for 3MF library
MOCK_FILES = [
    {
        "id": "file-001",
        "name": "benchy.3mf",
        "category": "Calibration",
        "uploaded": "2 hours ago",
        "size": "12.5 MB",
        "print_time": "2h 15m",
        "material": "PLA",
        "thumbnail": None
    },
    {
        "id": "file-002",
        "name": "phone_stand.3mf",
        "category": "Functional",
        "uploaded": "1 day ago",
        "size": "24.8 MB",
        "print_time": "4h 30m",
        "material": "PETG",
        "thumbnail": None
    },
    {
        "id": "file-003",
        "name": "vase_mode.3mf",
        "category": "Decorative",
        "uploaded": "3 days ago",
        "size": "8.2 MB",
        "print_time": "1h 45m",
        "material": "PLA",
        "thumbnail": None
    }
]

@router.get("")
async def get_files() -> List[dict]:
    """Get all files in the library"""
    return MOCK_FILES

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """Upload a 3MF file to the library"""
    if not file.filename.endswith('.3mf'):
        raise HTTPException(status_code=400, detail="Only .3MF files are allowed")
    
    # Mock file save
    return {"filename": file.filename}

@router.delete("/{file_id}")
async def delete_file(file_id: str) -> dict:
    """Delete a file from the library"""
    file = next((f for f in MOCK_FILES if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Mock file deletion
    return {"status": "success"}

@router.post("/print")
async def start_print(file_id: str, printer_id: str) -> dict:
    """Start printing a file on a specific printer"""
    file = next((f for f in MOCK_FILES if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # In real implementation, would check printer status and send file
    return {"status": "success"}
