"""
Main FastAPI application for the AI Core System.

This module creates and configures the FastAPI application with
all necessary middleware, CORS, authentication, and startup/shutdown events.
"""

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.endpoints import router as api_router
from .core.config import get_settings
from .core.logging import get_logger, setup_logging
from .core.redis_client import init_redis, close_redis
from .models.manager import get_model_manager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info("Starting AI Core System...")
    
    try:
        # Initialize Redis connection
        await init_redis()
        logger.info("Redis connection initialized")
        
        # Initialize model manager
        model_manager = await get_model_manager()
        logger.info("Model manager initialized")
        
        # Load default model if specified
        settings = get_settings()
        if settings.default_model:
            logger.info(f"Loading default model: {settings.default_model}")
            success = await model_manager.load_model(settings.default_model)
            if success:
                logger.info("Default model loaded successfully")
            else:
                logger.warning("Failed to load default model")
        
        logger.info("AI Core System started successfully")
        
    except Exception as e:
        logger.error("Failed to start AI Core System", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Core System...")
    
    try:
        # Close Redis connection
        await close_redis()
        logger.info("Redis connection closed")
        
        logger.info("AI Core System shutdown completed")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="AI Core System API",
        description="AI Core System for model inference and management",
        version="1.0.0",
        docs_url="/docs" if settings.enable_swagger else None,
        redoc_url="/redoc" if settings.enable_swagger else None,
        openapi_url="/openapi.json" if settings.enable_swagger else None,
        lifespan=lifespan
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
    
    # Add Gzip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=process_time
            )
            raise
    
    # Include API router
    app.include_router(api_router)
    
    # Add exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        logger.warning(
            "Validation error",
            errors=exc.errors(),
            path=request.url.path
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "timestamp": time.time(),
                "path": str(request.url.path),
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        )
    
    # Add health check endpoint (no authentication required)
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        try:
            # Check Redis connection
            from .core.redis_client import redis_client
            redis_healthy = False
            try:
                await redis_client.client.ping()
                redis_healthy = True
            except Exception:
                pass
            
            # Check model manager
            model_manager = await get_model_manager()
            models_data = await model_manager.list_models()
            loaded_models = [m for m in models_data if m["loaded"]]
            
            # Determine overall health
            overall_healthy = redis_healthy and len(loaded_models) > 0
            
            return {
                "status": "healthy" if overall_healthy else "unhealthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "redis": {"connected": redis_healthy},
                "models": {
                    "total": len(models_data),
                    "loaded": len(loaded_models)
                }
            }
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "error": str(e)
            }
    
    # Add root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "AI Core System API",
            "version": "1.0.0",
            "description": "AI Core System for model inference and management",
            "endpoints": {
                "api": "/api/v1",
                "health": "/health",
                "docs": "/docs" if settings.enable_swagger else None
            },
            "timestamp": time.time()
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    # Setup logging
    setup_logging()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload_on_change and settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    ) 