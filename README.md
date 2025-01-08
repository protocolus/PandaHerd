# PandaHerd: Bambu Lab Printer Farm Manager

A FastAPI-based management system for Bambu Lab 3D printer farms, providing real-time monitoring and management through a modern web interface.

## Features

- Modern, responsive dark-themed dashboard
- Real-time printer monitoring via WebSocket
- Detailed AMS status visualization
  - Filament color display
  - Real-time remaining percentage
  - Visual progress indicators
- Print job tracking with progress bars
- Printer status indicators
- Multi-printer control interface
- Context-aware printer controls (Start/Pause, Stop)
- RESTful API with OpenAPI documentation

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pandaherd.git
cd pandaherd
```

2. Build and start with Docker Compose:
```bash
docker-compose -f docker/docker-compose.yml up --build
```

3. Access the web interface at http://localhost:4373
   - Dashboard: http://localhost:4373
   - API Documentation: http://localhost:4373/docs

> **Note**: Port 4373 was chosen as it spells "HERD" on a phone keypad (4373), making it easy to remember!

## Development Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 4373
```

## API Documentation

The API documentation is automatically generated and available at `/docs`. It provides:
- Interactive API testing interface
- Request/response schemas
- Authentication methods (coming soon)
- Example requests and responses

> **Note**: The current version uses mock data for development. Future versions will integrate with real Bambu Lab printers via MQTT.

## Technology Stack

- **Backend**: FastAPI
- **Real-time Updates**: WebSocket
- **Frontend**: 
  - Tailwind CSS for styling
  - Vanilla JavaScript for interactivity
  - Real-time WebSocket client
- **Development**: 
  - Standard Python virtual environments
  - Docker for containerization
  - OpenAPI (Swagger) documentation

## Project Structure

```
PandaHerd/
├── core/               # Core functionality and configuration
├── routers/           # API route handlers
├── services/          # Business logic and services
├── static/            # Static assets
├── templates/         # HTML templates for the dashboard
├── main.py           # FastAPI application and WebSocket endpoints
├── schemas.py        # Pydantic models for API
├── version.py        # Version information
├── docker/           # Docker configuration files
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details
