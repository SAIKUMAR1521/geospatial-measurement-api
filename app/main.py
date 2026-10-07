from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="Geospatial File Measurement API",
    description="Production-grade API for uploading, processing, and measuring Shapefile (.zip) and KML (.kml) geospatial features with automatic projected CRS transformation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["Health Check"])
async def root_health_check():
    return {
        "service": "Geospatial File Measurement API",
        "status": "HEALTHY",
        "version": "1.0.0",
        "documentation": "/docs"
    }
