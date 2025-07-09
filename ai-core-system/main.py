"""
Main FastAPI application for the AI Core System.

This module creates and configures the FastAPI application with all
necessary middleware, routes, and startup/shutdown events.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import get_settings
from app.core.logging import get_logger, log_request
from app.api.routes import router as api_router
from app.models.manager import get_model_manager
from app.utils.redis_client import get_redis_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    settings = get_settings()
    
    # Startup
    logger.info("Starting AI Core System", version="1.0.0")
    
    try:
        # Initialize Redis connection
        redis_client = await get_redis_client()
        await redis_client.connect()
        logger.info("Redis connection established")
        
        # Initialize model manager
        model_manager = await get_model_manager()
        
        # Load default model if specified
        if settings.default_model:
            logger.info("Loading default model", model=settings.default_model)
            success = await model_manager.load_model(settings.default_model)
            if success:
                logger.info("Default model loaded successfully", model=settings.default_model)
            else:
                logger.warning("Failed to load default model", model=settings.default_model)
        
        logger.info("AI Core System started successfully")
        
    except Exception as e:
        logger.error("Failed to start AI Core System", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Core System")
    
    try:
        # Close Redis connection
        redis_client = await get_redis_client()
        await redis_client.disconnect()
        logger.info("Redis connection closed")
        
        logger.info("AI Core System shutdown complete")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="AI Core System",
        description="Modular AI Core System for Model Management and API Services",
        version="1.0.0",
        docs_url="/docs" if settings.enable_swagger_ui else None,
        redoc_url="/redoc" if settings.enable_redoc else None,
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    if settings.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add GZip middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests."""
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get API key (masked)
        api_key_header = settings.api_key_header
        api_key = request.headers.get(api_key_header, "")
        masked_api_key = api_key[:8] + "..." if len(api_key) > 8 else "***"
        
        # Process request
        try:
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Log successful request
            log_request(
                logger,
                request.method,
                str(request.url),
                response.status_code,
                processing_time,
                client_ip,
                user_agent,
                masked_api_key,
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log failed request
            log_request(
                logger,
                request.method,
                str(request.url),
                500,
                processing_time,
                client_ip,
                user_agent,
                masked_api_key,
            )
            
            raise
    
    # Add error handling middleware
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            url=str(request.url),
            method=request.method,
            client_ip=request.client.host if request.client else "unknown",
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP exception handler."""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            url=str(request.url),
            method=request.method,
            client_ip=request.client.host if request.client else "unknown",
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
    
    # Include API routes
    app.include_router(api_router)
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "AI Core System",
            "version": "1.0.0",
            "description": "Modular AI Core System for Model Management and API Services",
            "status": "running",
            "endpoints": {
                "api": "/api/v1",
                "docs": "/docs",
                "health": "/api/v1/health",
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    
    # Add health check endpoint (no authentication required)
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        try:
            # Check Redis
            redis_client = await get_redis_client()
            redis_healthy = await redis_client.health_check()
            
            # Check model manager
            model_manager = await get_model_manager()
            model_manager_health = await model_manager.health_check()
            
            status = "healthy" if redis_healthy and model_manager_health["status"] == "healthy" else "unhealthy"
            
            return {
                "status": status,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "services": {
                    "redis": "healthy" if redis_healthy else "unhealthy",
                    "model_manager": model_manager_health["status"],
                }
            }
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "error": str(e),
            }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload_on_change,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
        access_log=True,
    ) 