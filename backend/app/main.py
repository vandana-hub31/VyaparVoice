import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import (
    health,
    auth,
    businesses,
    dashboard,
    products,
    inventory,
    sales,
    customers,
    expenses,
    analytics,
    voice,
    demo
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("vyaparvoice")

app = FastAPI(
    title="VyaparVoice API",
    description="Multilingual Voice-First Business Management API for Small Indian Shopkeepers (Gnani AI Internship Challenge 2026)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Include Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(businesses.router)
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(customers.router)
app.include_router(expenses.router)
app.include_router(analytics.router)
app.include_router(voice.router)
app.include_router(demo.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to VyaparVoice API — Your Shop, Ready to Speak",
        "documentation": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
