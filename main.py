from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
from typing import List
import asyncio
from fastapi import WebSocketDisconnect
from version import VERSION
from routers import printers, jobs
import qrcode
import qrcode.image.svg
import base64
from io import BytesIO

app = FastAPI(
    title="PandaHerd",
    description="Bambu Lab Printer Farm Manager",
    version=VERSION,
)

# Create templates directory if it doesn't exist
templates_dir = Path("templates")
templates_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory=str(templates_dir))

# Include routers
app.include_router(printers.router)
app.include_router(jobs.router)

def generate_qr_code(spool_id: str) -> str:
    """Generate QR code for a spool as base64 SVG"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    # URL will open the weight modal directly
    qr.add_data(f"pandaherd://weigh/{spool_id}")
    qr.make(fit=True)

    # Create SVG image
    img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
    stream = BytesIO()
    img.save(stream)
    svg_string = stream.getvalue().decode()
    return svg_string

# Mock data for filament inventory
MOCK_FILAMENT = [
    {
        "id": "RFID-01234567",  # This would come from the AMS RFID reader
        "name": "Bambu PLA",
        "brand": "Bambu Lab",
        "material": "PLA",
        "color": "#00AE42",
        "color_name": "Bambu Green",
        "remaining_pct": 92,
        "initial_weight_g": 1000,
        "empty_spool_g": 250,
        "printer": "Printer 1",
        "slot": 1,
        "last_used": "2 hours ago"
    },
    {
        "id": "RFID-89ABCDEF",
        "name": "Galaxy PLA",
        "brand": "Bambu Lab",
        "material": "PLA",
        "color": "#0A2989",
        "color_name": "Deep Blue",
        "remaining_pct": 78,
        "initial_weight_g": 1000,
        "empty_spool_g": 250,
        "printer": "Printer 1",
        "slot": 2,
        "last_used": "1 day ago"
    },
    {
        "id": "RFID-12345678",
        "name": "Fire Engine Red",
        "brand": "Bambu Lab",
        "material": "PETG",
        "color": "#C12E1F",
        "color_name": "Red",
        "remaining_pct": 45,
        "initial_weight_g": 1000,
        "empty_spool_g": 250,
        "printer": "Printer 1",
        "slot": 3,
        "last_used": "3 days ago"
    },
    {
        "id": "RFID-90123456",
        "name": "Ninja TPU",
        "brand": "Bambu Lab",
        "material": "TPU",
        "color": "#000000",
        "color_name": "Black",
        "remaining_pct": 88,
        "initial_weight_g": 500,
        "empty_spool_g": 250,
        "printer": "Printer 1",
        "slot": 4,
        "last_used": "1 week ago"
    },
    {
        "id": "RFID-11111111",
        "name": "Snow White",
        "brand": "PolyTerra",
        "material": "PLA",
        "color": "#FFFFFF",
        "color_name": "White",
        "remaining_pct": 15,
        "initial_weight_g": 1000,
        "empty_spool_g": 180,
        "printer": None,
        "slot": None,
        "last_used": "2 weeks ago"
    },
    {
        "id": "RFID-22222222",
        "name": "Gold Rush",
        "brand": "PolyTerra",
        "material": "PLA",
        "color": "#FFD700",
        "color_name": "Gold",
        "remaining_pct": 5,
        "initial_weight_g": 1000,
        "empty_spool_g": 180,
        "printer": None,
        "slot": None,
        "last_used": "1 month ago"
    }
]

# Mock data - in real app this would come from MQTT
MOCK_PRINTERS = {
    "printer1": {
        "name": "Printer 1",
        "status": "printing",
        "current_job": {
            "name": "benchy.3mf",
            "progress": 45
        },
        "ams": {
            "slots": [
                {"color": "#00AE42", "remaining": 92},
                {"color": "#0A2989", "remaining": 78},
                {"color": "#C12E1F", "remaining": 45},
                {"color": "#000000", "remaining": 88}
            ]
        }
    },
    "printer2": {
        "name": "Printer 2",
        "status": "paused",
        "current_job": {
            "name": "calibration_cube.3mf",
            "progress": 75
        },
        "ams": {
            "slots": [
                {"color": "#FFFFFF", "remaining": 95},
                {"color": "#FFD700", "remaining": 82},
                {"color": "#4B0082", "remaining": 67},
                {"color": "#808080", "remaining": 91}
            ]
        }
    },
    "printer3": {
        "name": "Printer 3",
        "status": "idle",
        "current_job": None,
        "ams": {
            "slots": [
                {"color": "#32CD32", "remaining": 88},
                {"color": "#1E90FF", "remaining": 72},
                {"color": "#DC143C", "remaining": 55},
                {"color": "#696969", "remaining": 93}
            ]
        }
    }
}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # In a real app, this would be updated from MQTT
            await websocket.send_json(MOCK_PRINTERS)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "printers": MOCK_PRINTERS,
            "total_printers": len(MOCK_PRINTERS),
            "online_printers": sum(1 for p in MOCK_PRINTERS.values() if p["status"] != "offline"),
            "version": VERSION,
            "active_page": "dashboard"
        }
    )

@app.get("/filament", response_class=HTMLResponse)
async def filament(request: Request):
    """Filament inventory page"""
    # Generate QR codes for each spool
    spools_with_qr = []
    for spool in MOCK_FILAMENT:
        spool_copy = dict(spool)
        spool_copy["qr_code"] = generate_qr_code(spool["id"])
        spools_with_qr.append(spool_copy)
    
    total_weight = sum(spool["remaining_pct"] / 100 * (spool["initial_weight_g"] - spool["empty_spool_g"]) 
                      for spool in MOCK_FILAMENT)
    low_stock = [s for s in MOCK_FILAMENT if s["remaining_pct"] <= 20]
    
    return templates.TemplateResponse(
        "filament.html",
        {
            "request": request,
            "spools": spools_with_qr,
            "total_spools": len(MOCK_FILAMENT),
            "total_weight": round(total_weight, 1),
            "low_stock_count": len(low_stock),
            "version": VERSION,
            "active_page": "filament"
        }
    )

@app.get("/api/filament")
async def get_filament():
    """API endpoint for filament inventory"""
    return {
        "spools": MOCK_FILAMENT,
        "total_spools": len(MOCK_FILAMENT),
        "total_weight": round(sum(spool["remaining_pct"] / 100 * (spool["initial_weight_g"] - spool["empty_spool_g"]) for spool in MOCK_FILAMENT), 1),
        "low_stock_count": len([s for s in MOCK_FILAMENT if s["remaining_pct"] <= 20])
    }

@app.get("/api/filament/{spool_id}/qr")
async def get_spool_qr(spool_id: str):
    """Get QR code for a spool"""
    spool = next((s for s in MOCK_FILAMENT if s["id"] == spool_id), None)
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    return {"qr_code": generate_qr_code(spool_id)}

@app.post("/api/filament/{spool_id}/weight")
async def update_spool_weight(spool_id: str, total_weight_g: float):
    """Update spool weight and recalculate remaining percentage"""
    spool = next((s for s in MOCK_FILAMENT if s["id"] == spool_id), None)
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    
    if total_weight_g < spool["empty_spool_g"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Total weight ({total_weight_g}g) cannot be less than empty spool weight ({spool['empty_spool_g']}g)"
        )
    
    # Calculate remaining percentage based on weight
    filament_weight = total_weight_g - spool["empty_spool_g"]
    max_filament = spool["initial_weight_g"] - spool["empty_spool_g"]
    spool["remaining_pct"] = round((filament_weight / max_filament) * 100)
    
    return spool
