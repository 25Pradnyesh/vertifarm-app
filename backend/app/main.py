import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.services.mqtt_service import mqtt_service
from app.services.realtime_service import realtime_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bind running event loop to realtime service
    loop = asyncio.get_running_loop()
    realtime_service.set_loop(loop)

    # Start MQTT background ingestion service if MQTT_ENABLED=true
    mqtt_service.start()
    yield
    # Stop MQTT background ingestion service
    mqtt_service.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Precision Vertical Farming Environmental Monitoring and Agricultural Intelligence API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

# Root info endpoint
@app.get("/", tags=["Info"])
def root_info():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": f"{settings.API_V1_STR}/docs",
    }

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
