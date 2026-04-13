from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.models import Corporation, Facility, CorporationFinancial, DataCollectionLog
from app.routers import corporations, facilities, analytics, collection_logs
from app.scheduler import start_scheduler, stop_scheduler

# Create tables
Base.metadata.create_all(bind=engine)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✓ Application startup")
    start_scheduler()
    yield
    print("✓ Application shutdown")
    stop_scheduler()


# Initialize FastAPI app
app = FastAPI(
    title=os.getenv("API_TITLE", "Welfare Facilities DB"),
    version=os.getenv("API_VERSION", "0.1.0"),
    description="Social welfare facilities database API",
    lifespan=lifespan
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000"]')
try:
    import json
    origins = json.loads(cors_origins)
except:
    origins = ["http://localhost:5173", "http://localhost:3000"]

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
