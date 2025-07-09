"""
Main FastAPI application for the AI Core System.

This module creates and configures the FastAPI application with all
necessary middleware, routes, and startup/shutdown events.
"""

import time
import os
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

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    settings = get_settings()
    
    # Startup
    logger.info("Starting AI Core System", version="1.0.0")
    
    try:
        logger.info("AI Core System started successfully")
        
    except Exception as e:
        logger.error("Failed to start AI Core System", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Core System")
    
    try:
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
                "***",
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
                "***",
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
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "AI Core System is running!",
            "version": "1.0.0",
            "status": "healthy"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "ai-core-system",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=settings.api_workers,
    ) 