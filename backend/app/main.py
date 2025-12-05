from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ecommerce, shortage, pharmacies
from app.core.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Dashboard Partners API",
    description="API para métricas de partners de LudaFarma",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include routers
app.include_router(
    ecommerce.router, 
    prefix="/api/ecommerce", 
    tags=["Ecommerce"]
)
app.include_router(
    shortage.router, 
    prefix="/api/shortage", 
    tags=["Shortage"]
)
app.include_router(
    pharmacies.router, 
    prefix="/api/pharmacies", 
    tags=["Pharmacies"]
)

@app.get("/")
async def root():
    return {
        "message": "Dashboard Partners API - LudaFarma",
        "version": "2.0.0",
        "endpoints": {
            "ecommerce": "/api/ecommerce",
            "shortage": "/api/shortage",
            "pharmacies": "/api/pharmacies",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
