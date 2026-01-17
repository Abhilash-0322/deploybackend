"""
AI Compliance Agent for Aptos dApps

FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.api.routes import contracts, transactions, compliance, demo, agents, workflows, prices
from app.api.websocket import websocket_endpoint
from app.core.transaction_monitor import get_transaction_monitor
from app.core.database import connect_to_mongodb, close_mongodb_connection
from app.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    print(f"🚀 Starting Aptos Compliance Agent")
    print(f"📡 Connected to: {settings.aptos_network}")
    print(f"🤖 AI Analysis: {'Enabled (Groq)' if settings.groq_api_key else 'Disabled (no API key)'}")
    print(f"🎯 Demo contracts available at /api/demo/contracts")
    
    # Connect to MongoDB
    await connect_to_mongodb()
    
    # Start transaction monitor
    monitor = get_transaction_monitor()
    await monitor.start()
    print("📊 Transaction monitor started")
    
    yield
    
    # Shutdown
    await monitor.stop()
    await close_mongodb_connection()
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Aptos Compliance Agent",
    description="AI-powered compliance and security agent for Aptos dApps",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware - use settings
settings = get_settings()
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(contracts.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(workflows.router)
app.include_router(prices.router, prefix="/api")


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts."""
    await websocket_endpoint(websocket)


# Health check
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        aptos_network=settings.aptos_network,
        ai_enabled=bool(settings.groq_api_key)
    )

from pathlib import Path

# Serve static frontend files
# The static directory should contain the built Next.js export
# Try multiple possible locations for the static directory
possible_static_dirs = [
    Path(__file__).parent.parent / "static",  # ../static from app/main.py
    Path.cwd() / "static",                     # ./static from working directory
    Path("/app/static"),                        # Docker container path
]

static_dir = None
for dir_path in possible_static_dirs:
    if dir_path.exists() and dir_path.is_dir():
        # Verify it has index.html (Next.js export)
        if (dir_path / "index.html").exists():
            static_dir = str(dir_path.resolve())
            break

if static_dir:
    print(f"📁 Found static frontend at: {static_dir}")
    # List contents for debugging
    static_contents = list(Path(static_dir).iterdir())
    print(f"   Contents: {[f.name for f in static_contents[:10]]}{'...' if len(static_contents) > 10 else ''}")
    
    # Mount static files at root - this MUST come after all API routes
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    print(f"✅ Static frontend mounted at /")
else:
    print("⚠️  No static frontend found. Checked:")
    for dir_path in possible_static_dirs:
        print(f"   - {dir_path} (exists: {dir_path.exists()})")
    
    # Fallback API root when no static files
    @app.get("/", tags=["API"])
    async def root():
        """API root endpoint - redirects to docs."""
        return {
            "message": "Aptos Compliance Agent API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/health",
            "note": "No static frontend found. Build the frontend and copy to /static"
        }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
