from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os
import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger

from app.database import engine, Base
from app.models import Corporation, Facility, CorporationFinancial, DataCollectionLog
from app.routers import corporations, facilities, analytics, collection_logs, monitoring
from app.scheduler import start_scheduler, stop_scheduler

# Setup structured logging
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# Application start time for uptime calculation
APP_START_TIME = datetime.utcnow()

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize Prometheus instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health", "/docs", "/openapi.json"],
)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    start_scheduler()
    yield
    logger.info("Application shutdown")
    stop_scheduler()


# Initialize FastAPI app
app = FastAPI(
    title=os.getenv("API_TITLE", "Welfare Facilities DB"),
    version=os.getenv("API_VERSION", "0.1.0"),
    description="Social welfare facilities database API",
    lifespan=lifespan
)

# Instrument the app with Prometheus metrics
instrumentator.instrument(app)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000"]')
try:
    import json
    origins = json.loads(cors_origins)
except:
    origins = ["http://localhost:5173", "http://localhost:3000"]

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info("http_request", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round(duration * 1000, 2),
    })
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(corporations.router)
app.include_router(facilities.router)
app.include_router(analytics.router)
app.include_router(collection_logs.router)
app.include_router(monitoring.router)


@app.get("/")
def read_root():
    """API root endpoint"""
    return {
        "message": "Welfare Facilities DB API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "welfare-facilities-db"
    }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
