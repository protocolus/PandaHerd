from fastapi import APIRouter, HTTPException
from typing import Dict, List
from models.filament import FilamentSpool

router = APIRouter(prefix="/filament", tags=["filament"])

# In-memory storage for filament spools
spools: Dict[str, FilamentSpool] = {}

@router.post("/spools/")
async def create_spool(spool: FilamentSpool):
    """Create a new filament spool"""
    spools[spool.id] = spool
    return spool

@router.get("/spools/{spool_id}")
async def get_spool(spool_id: str):
    """Get a filament spool by ID"""
    if spool_id not in spools:
        raise HTTPException(status_code=404, detail="Spool not found")
    return spools[spool_id]

@router.post("/spools/{spool_id}/usage")
async def record_usage(
    spool_id: str, 
    job_name: str,
    grams_used: float,
    purge_tower_grams: float = 0.0,
    notes: str = None
):
    """Record filament usage for a print job"""
    if spool_id not in spools:
        raise HTTPException(status_code=404, detail="Spool not found")
    
    spool = spools[spool_id]
    spool.record_usage(job_name, grams_used, purge_tower_grams, notes)
    return spool

@router.post("/spools/{spool_id}/weight")
async def record_weight(
    spool_id: str,
    total_weight_g: float,
    notes: str = None
):
    """Record a manual weight measurement for a spool"""
    if spool_id not in spools:
        raise HTTPException(status_code=404, detail="Spool not found")
    
    try:
        spool = spools[spool_id]
        spool.record_weight(total_weight_g, notes)
        return spool
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
