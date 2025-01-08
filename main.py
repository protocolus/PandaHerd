from fastapi import FastAPI, Request, WebSocket, HTTPException, File, UploadFile
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
from services.analyzer import ThreeMFAnalyzer

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

def generate_qr_code(data: str, size: int = 10) -> str:
    """Generate QR code as base64 SVG
    
    Args:
        data: String to encode in QR code
        size: Size of QR code in cm
        
    Returns:
        Base64 encoded SVG string
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create SVG image
    img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer)
    
    # Return as base64 data URL
    svg_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/svg+xml;base64,{svg_base64}"

@app.get("/api/qrcode")
async def get_qr_code(data: str, size: int = 10):
    """Generate QR code for any data
    
    Args:
        data: String to encode
        size: Size in cm (default: 10)
    """
    try:
        qr_code = generate_qr_code(data, size)
        return {"qr_code": qr_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Example for filament spool QR codes
@app.get("/api/filament/{spool_id}/qr")
async def get_spool_qr(spool_id: str):
    """Get QR code for a filament spool
    
    The QR code contains a URL to quickly access the spool's weight update page:
    pandaherd://filament/spool/{id}/weight
    """
    spool = next((s for s in MOCK_FILAMENT if s["id"] == spool_id), None)
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
        
    # Generate URL for spool weight update
    data = f"pandaherd://filament/spool/{spool_id}/weight"
    qr_code = generate_qr_code(data)
    
    return {
        "qr_code": qr_code,
        "data": data
    }

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
        "thumbnail": None,
        "dimensions": {
            "width": 60.0,
            "depth": 31.0,
            "height": 48.0
        },
        "volume_cm3": 15.8,
        "vertices": 27644,
        "triangles": 55288,
        "print_settings": {
            "layer_height": "0.2",
            "infill_density": "20",
            "nozzle_temperature": "215",
            "bed_temperature": "60",
            "supports": "none",
            "adhesion_type": "brim"
        },
        "estimated_material_grams": 18.9,
        "bambu_metadata": {
            "ams_mapping": [
                {
                    "ams_slot": 0,
                    "type": "PLA",
                    "color": "#FF0000",
                    "temperature": 215,
                    "weight_used": 18.9,
                    "name": "Red PLA"
                }
            ],
            "plate_info": {
                "plate_type": "smooth",
                "bed_temp": 60,
                "chamber_temp": 0,
                "first_layer_bed_temp": 60
            },
            "print_params": {
                "layer_height": 0.2,
                "initial_layer_height": 0.2,
                "perimeters": 3,
                "infill_density": 20,
                "support_type": "normal",
                "enable_support": False,
                "brim_type": "brim",
                "brim_width": 5
            }
        }
    },
    {
        "id": "file-002",
        "name": "phone_stand.3mf",
        "category": "Functional",
        "uploaded": "1 day ago",
        "size": "24.8 MB",
        "print_time": "4h 30m",
        "material": "PETG",
        "thumbnail": None,
        "dimensions": {
            "width": 85.0,
            "depth": 120.0,
            "height": 75.0
        },
        "volume_cm3": 45.2,
        "vertices": 42156,
        "triangles": 84312,
        "print_settings": {
            "layer_height": "0.2",
            "infill_density": "30",
            "nozzle_temperature": "240",
            "bed_temperature": "80",
            "supports": "minimal",
            "adhesion_type": "skirt"
        },
        "estimated_material_grams": 54.2,
        "bambu_metadata": {
            "ams_mapping": [
                {
                    "ams_slot": 1,
                    "type": "PETG",
                    "color": "#000000",
                    "temperature": 240,
                    "weight_used": 54.2,
                    "name": "Black PETG"
                }
            ],
            "plate_info": {
                "plate_type": "textured",
                "bed_temp": 80,
                "chamber_temp": 0,
                "first_layer_bed_temp": 85
            },
            "print_params": {
                "layer_height": 0.2,
                "initial_layer_height": 0.2,
                "perimeters": 4,
                "infill_density": 30,
                "support_type": "normal",
                "enable_support": True,
                "brim_type": "skirt",
                "brim_width": 0
            }
        }
    },
    {
        "id": "file-003",
        "name": "vase_mode.3mf",
        "category": "Decorative",
        "uploaded": "3 days ago",
        "size": "8.2 MB",
        "print_time": "1h 45m",
        "material": "PLA",
        "thumbnail": None,
        "dimensions": {
            "width": 100.0,
            "depth": 100.0,
            "height": 150.0
        },
        "volume_cm3": 8.5,
        "vertices": 15422,
        "triangles": 30844,
        "print_settings": {
            "layer_height": "0.2",
            "infill_density": "0",
            "nozzle_temperature": "210",
            "bed_temperature": "60",
            "supports": "none",
            "adhesion_type": "brim",
            "special_mode": "spiralize"
        },
        "estimated_material_grams": 10.2,
        "bambu_metadata": {
            "ams_mapping": [
                {
                    "ams_slot": 2,
                    "type": "PLA",
                    "color": "#00FF00",
                    "temperature": 210,
                    "weight_used": 10.2,
                    "name": "Green PLA"
                }
            ],
            "plate_info": {
                "plate_type": "smooth",
                "bed_temp": 60,
                "chamber_temp": 0,
                "first_layer_bed_temp": 65
            },
            "print_params": {
                "layer_height": 0.2,
                "initial_layer_height": 0.2,
                "perimeters": 2,
                "infill_density": 0,
                "support_type": "none",
                "enable_support": False,
                "brim_type": "brim",
                "brim_width": 3
            }
        }
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

@app.get("/library", response_class=HTMLResponse)
async def library(request: Request):
    """3MF file library page"""
    return templates.TemplateResponse(
        "library.html",
        {
            "request": request,
            "files": MOCK_FILES,
            "printers": MOCK_PRINTERS.values(),
            "version": VERSION,
            "active_page": "library"
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

@app.post("/api/library/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a 3MF file to the library"""
    if not file.filename.endswith('.3mf'):
        raise HTTPException(status_code=400, detail="Only .3MF files are allowed")
    
    # Read file content
    content = await file.read()
    
    # Analyze the file
    try:
        with ThreeMFAnalyzer(file_content=content) as analyzer:
            analysis = analyzer.analyze()
            
            # Create mock file entry with analysis data
            new_file = {
                "id": f"file-{len(MOCK_FILES) + 1:03d}",
                "name": file.filename,
                "category": "Uncategorized",
                "uploaded": "Just now",
                "size": f"{len(content) / 1024 / 1024:.1f} MB",
                "print_time": analysis['model_info'].get('estimated_print_time', 'Unknown'),
                "material": analysis['print_settings'].get('material', 'PLA'),
                "thumbnail": analysis.get('thumbnail'),
                "dimensions": analysis['model_info'].get('dimensions', {}),
                "volume_cm3": analysis['model_info'].get('volume_cm3', 0),
                "vertices": analysis['model_info'].get('vertices', 0),
                "triangles": analysis['model_info'].get('triangles', 0),
                "print_settings": analysis['print_settings'],
                "bambu_metadata": analysis.get('bambu_metadata', {})
            }
            
            MOCK_FILES.append(new_file)
            return new_file
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to analyze file: {str(e)}")

@app.get("/api/library/{file_id}/analysis")
async def get_file_analysis(file_id: str):
    """Get detailed analysis of a file"""
    file = next((f for f in MOCK_FILES if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "dimensions": file.get("dimensions", {}),
        "volume_cm3": file.get("volume_cm3", 0),
        "vertices": file.get("vertices", 0),
        "triangles": file.get("triangles", 0),
        "print_settings": file.get("print_settings", {})
    }

@app.post("/api/library/print")
async def start_print(file_id: str, printer_id: str):
    """Start printing a file on a specific printer"""
    file = next((f for f in MOCK_FILES if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    printer = MOCK_PRINTERS.get(printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if printer["status"] == "printing":
        raise HTTPException(status_code=400, detail="Printer is already printing")
    
    # Mock print start
    printer["status"] = "printing"
    printer["current_job"] = {
        "name": file["name"],
        "progress": 0
    }
    
    return {"status": "success"}

@app.delete("/api/library/{file_id}")
async def delete_file(file_id: str):
    """Delete a file from the library"""
    file = next((f for f in MOCK_FILES if f["id"] == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Mock file deletion
    return {"status": "success"}
