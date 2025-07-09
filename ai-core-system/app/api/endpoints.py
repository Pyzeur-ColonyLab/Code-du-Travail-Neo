"""
API endpoints for the AI Core System.

This module contains all FastAPI endpoints for model inference,
management, and system monitoring.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from .models import (
    GenerateRequest, GenerateResponse,
    ChatRequest, ChatResponse, ChatMessage,
    ModelLoadRequest, ModelLoadResponse,
    ModelUnloadRequest, ModelUnloadResponse,
    ModelListResponse, ModelInfo,
    HealthResponse, MetricsResponse,
    ErrorResponse, SuccessResponse
)
from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.redis_client import redis_client
from ..models.manager import get_model_manager

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["AI Core API"])

# Global variables for metrics
start_time = time.time()
request_count = 0
error_count = 0
response_times = []


async def get_api_key(request: Request) -> str:
    """Extract and validate API key from request headers."""
    settings = get_settings()
    api_key = request.headers.get(settings.api_key_header)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Validate API key (simple validation for now)
    valid_keys = [settings.default_api_key, settings.admin_api_key]
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(
    request: GenerateRequest,
    api_key: str = Depends(get_api_key)
) -> GenerateResponse:
    """
    Generate text using AI models.
    
    Args:
        request: Generation request parameters
        api_key: Validated API key
        
    Returns:
        Generated text response
    """
    global request_count, error_count, response_times
    
    start_time_request = time.time()
    request_count += 1
    
    try:
        settings = get_settings()
        model_manager = await get_model_manager()
        
        # Check cache first
        cache_key = f"generate:{hash(request.json())}"
        cached_response = await redis_client.get(cache_key)
        
        if cached_response:
            logger.info("Serving cached response", cache_key=cache_key)
            return GenerateResponse(
                response=cached_response["response"],
                model=cached_response["model"],
                tokens_used=cached_response.get("tokens_used"),
                processing_time=cached_response.get("processing_time"),
                cached=True
            )
        
        # Generate response
        model_name = request.model or settings.default_model
        
        response_text = await model_manager.generate(
            prompt=request.prompt,
            model_name=model_name,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop_tokens=request.stop_tokens
        )
        
        if not response_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            )
        
        processing_time = time.time() - start_time_request
        
        # Cache response
        cache_data = {
            "response": response_text,
            "model": model_name,
            "tokens_used": len(response_text.split()),  # Approximate
            "processing_time": processing_time
        }
        await redis_client.set(cache_key, cache_data, ttl=settings.cache_ttl)
        
        # Update metrics
        response_times.append(processing_time)
        if len(response_times) > 100:  # Keep only last 100 requests
            response_times.pop(0)
        
        logger.info("Text generation completed", 
                   model=model_name, processing_time=processing_time)
        
        return GenerateResponse(
            response=response_text,
            model=model_name,
            tokens_used=len(response_text.split()),  # Approximate
            processing_time=processing_time,
            cached=False
        )
        
    except HTTPException:
        error_count += 1
        raise
    except Exception as e:
        error_count += 1
        logger.error("Generation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(get_api_key)
) -> ChatResponse:
    """
    Chat with AI models using conversation history.
    
    Args:
        request: Chat request with message history
        api_key: Validated API key
        
    Returns:
        Chat response with updated conversation
    """
    global request_count, error_count, response_times
    
    start_time_request = time.time()
    request_count += 1
    
    try:
        settings = get_settings()
        model_manager = await get_model_manager()
        
        # Format conversation for the model
        conversation = ""
        for message in request.messages:
            if message.role == "user":
                conversation += f"User: {message.content}\n"
            elif message.role == "assistant":
                conversation += f"Assistant: {message.content}\n"
            elif message.role == "system":
                conversation += f"System: {message.content}\n"
        
        conversation += "Assistant: "
        
        # Generate response
        model_name = request.model or settings.default_model
        
        response_text = await model_manager.generate(
            prompt=conversation,
            model_name=model_name,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop_tokens=request.stop_tokens
        )
        
        if not response_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate chat response"
            )
        
        # Update conversation history
        updated_messages = request.messages + [
            ChatMessage(role="assistant", content=response_text)
        ]
        
        processing_time = time.time() - start_time_request
        
        # Update metrics
        response_times.append(processing_time)
        if len(response_times) > 100:
            response_times.pop(0)
        
        logger.info("Chat completed", 
                   model=model_name, processing_time=processing_time)
        
        return ChatResponse(
            response=response_text,
            model=model_name,
            messages=updated_messages,
            tokens_used=len(response_text.split()),  # Approximate
            processing_time=processing_time
        )
        
    except HTTPException:
        error_count += 1
        raise
    except Exception as e:
        error_count += 1
        logger.error("Chat error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    api_key: str = Depends(get_api_key)
) -> ModelListResponse:
    """
    List all available models with their status.
    
    Args:
        api_key: Validated API key
        
    Returns:
        List of models with status information
    """
    try:
        model_manager = await get_model_manager()
        models_data = await model_manager.list_models()
        
        # Convert to ModelInfo objects
        models = []
        loaded_count = 0
        
        for model_data in models_data:
            if model_data["loaded"]:
                loaded_count += 1
            
            models.append(ModelInfo(**model_data))
        
        return ModelListResponse(
            models=models,
            current_model=model_manager.current_model,
            total_models=len(models),
            loaded_models=loaded_count
        )
        
    except Exception as e:
        logger.error("Error listing models", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.post("/models/load", response_model=ModelLoadResponse)
async def load_model(
    request: ModelLoadRequest,
    api_key: str = Depends(get_api_key)
) -> ModelLoadResponse:
    """
    Load a model into memory.
    
    Args:
        request: Model loading request
        api_key: Validated API key
        
    Returns:
        Model loading response
    """
    try:
        model_manager = await get_model_manager()
        
        # Check if model is already loaded
        if request.model in model_manager.models and not request.force:
            return ModelLoadResponse(
                success=True,
                model=request.model,
                load_time=0.0,
                message="Model already loaded"
            )
        
        # Force unload if requested
        if request.force and request.model in model_manager.models:
            await model_manager.unload_model(request.model)
        
        # Load model
        start_time_load = time.time()
        success = await model_manager.load_model(request.model)
        load_time = time.time() - start_time_load
        
        if success:
            logger.info("Model loaded successfully", 
                       model=request.model, load_time=load_time)
            
            return ModelLoadResponse(
                success=True,
                model=request.model,
                load_time=load_time,
                message="Model loaded successfully"
            )
        else:
            logger.error("Failed to load model", model=request.model)
            
            return ModelLoadResponse(
                success=False,
                model=request.model,
                load_time=load_time,
                message="Failed to load model"
            )
        
    except Exception as e:
        logger.error("Error loading model", model=request.model, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}"
        )


@router.post("/models/unload", response_model=ModelUnloadResponse)
async def unload_model(
    request: ModelUnloadRequest,
    api_key: str = Depends(get_api_key)
) -> ModelUnloadResponse:
    """
    Unload a model from memory.
    
    Args:
        request: Model unloading request
        api_key: Validated API key
        
    Returns:
        Model unloading response
    """
    try:
        model_manager = await get_model_manager()
        
        success = await model_manager.unload_model(request.model)
        
        if success:
            logger.info("Model unloaded successfully", model=request.model)
            
            return ModelUnloadResponse(
                success=True,
                model=request.model,
                message="Model unloaded successfully"
            )
        else:
            logger.error("Failed to unload model", model=request.model)
            
            return ModelUnloadResponse(
                success=False,
                model=request.model,
                message="Failed to unload model"
            )
        
    except Exception as e:
        logger.error("Error unloading model", model=request.model, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}"
        )


@router.get("/models/{model_name}/status")
async def get_model_status(
    model_name: str,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """
    Get detailed status of a specific model.
    
    Args:
        model_name: Name of the model
        api_key: Validated API key
        
    Returns:
        Detailed model status
    """
    try:
        model_manager = await get_model_manager()
        status = await model_manager.get_model_status(model_name)
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model_name}' not found"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting model status", model=model_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model status: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        System health status
    """
    try:
        settings = get_settings()
        model_manager = await get_model_manager()
        
        # Check Redis connection
        redis_healthy = False
        redis_info = {}
        try:
            redis_info = await redis_client.info()
            redis_healthy = True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
        
        # Get model status
        models_data = await model_manager.list_models()
        loaded_models = [m for m in models_data if m["loaded"]]
        
        # Calculate uptime
        uptime = time.time() - start_time
        
        # Get memory usage (simplified)
        import psutil
        memory_info = {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        }
        
        # Determine overall health
        overall_healthy = redis_healthy and len(loaded_models) > 0
        
        return HealthResponse(
            status="healthy" if overall_healthy else "unhealthy",
            version="1.0.0",
            uptime=uptime,
            models={
                "total": len(models_data),
                "loaded": len(loaded_models),
                "current": model_manager.current_model
            },
            redis={
                "connected": redis_healthy,
                "info": redis_info
            },
            memory=memory_info
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            uptime=time.time() - start_time,
            models={},
            redis={"connected": False, "info": {}},
            memory={}
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    api_key: str = Depends(get_api_key)
) -> MetricsResponse:
    """
    Get system metrics.
    
    Args:
        api_key: Validated API key
        
    Returns:
        System metrics
    """
    try:
        # Calculate metrics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0
        
        # Get model usage stats
        model_manager = await get_model_manager()
        models_data = await model_manager.list_models()
        model_usage = {
            "total_models": len(models_data),
            "loaded_models": len([m for m in models_data if m["loaded"]]),
            "current_model": model_manager.current_model
        }
        
        # Get cache stats
        cache_keys = await redis_client.keys("generate:*")
        cache_stats = {
            "total_cached_responses": len(cache_keys),
            "cache_hit_rate": 0.0  # Would need to track hits/misses
        }
        
        # Get memory stats
        import psutil
        memory_usage = {
            "total_mb": psutil.virtual_memory().total / (1024 * 1024),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "percent_used": psutil.virtual_memory().percent
        }
        
        return MetricsResponse(
            requests_total=request_count,
            requests_per_minute=request_count / ((time.time() - start_time) / 60),
            average_response_time=avg_response_time,
            error_rate=error_rate,
            memory_usage=memory_usage,
            model_usage=model_usage,
            cache_stats=cache_stats
        )
        
    except Exception as e:
        logger.error("Error getting metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.
    
    Returns:
        API information
    """
    return {
        "name": "AI Core System API",
        "version": "1.0.0",
        "description": "AI Core System for model inference and management",
        "endpoints": {
            "generate": "/api/v1/generate",
            "chat": "/api/v1/chat",
            "models": "/api/v1/models",
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics"
        },
        "documentation": "/docs"
    }


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            details={"path": request.url.path}
        ).dict()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"path": request.url.path}
        ).dict()
    ) 