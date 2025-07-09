"""
FastAPI routes for the AI Core System.

This module contains all API endpoints for model inference,
management, monitoring, and system administration.
"""

import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.responses import StreamingResponse
import psutil

from .models import (
    GenerationRequest, GenerationResponse,
    ChatRequest, ChatResponse,
    ModelLoadRequest, ModelLoadResponse,
    ModelUnloadRequest, ModelUnloadResponse,
    ModelListResponse, ModelStatusResponse,
    HealthResponse, MetricsResponse,
    ErrorResponse, RateLimitResponse,
    WebhookRequest, WebhookResponse,
    StreamChunk, BatchRequest, BatchResponse,
    SessionRequest, SessionResponse,
    ModelInfo
)
from ..core.config import get_settings
from ..core.logging import get_logger, log_request, log_security_event
from ..models.manager import get_model_manager, GenerationConfig
from ..utils.redis_client import get_redis_client

logger = get_logger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["AI Core API"])

# Global metrics
request_count = 0
start_time = time.time()
model_usage = {}


async def verify_api_key(request: Request) -> str:
    """Verify API key from request header."""
    settings = get_settings()
    api_key_header = settings.api_key_header
    
    api_key = request.headers.get(api_key_header)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if api_key not in settings.api_keys:
        log_security_event(
            logger,
            "invalid_api_key",
            request.client.host if request.client else "unknown",
            request.headers.get("user-agent", "unknown"),
            {"api_key": api_key[:8] + "..." if len(api_key) > 8 else "***"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


async def check_rate_limit(request: Request, api_key: str) -> None:
    """Check rate limiting for the API key."""
    settings = get_settings()
    redis_client = await get_redis_client()
    
    # Create rate limit key
    rate_key = f"rate_limit:{api_key}:{int(time.time() // 60)}"
    
    # Get current count
    current_count = await redis_client.get(rate_key, deserialize=False, default=0)
    if isinstance(current_count, bytes):
        current_count = int(current_count.decode())
    else:
        current_count = int(current_count or 0)
    
    # Check if limit exceeded
    if current_count >= settings.rate_limit_per_minute:
        log_security_event(
            logger,
            "rate_limit_exceeded",
            request.client.host if request.client else "unknown",
            request.headers.get("user-agent", "unknown"),
            {"api_key": api_key[:8] + "...", "count": current_count}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Increment counter
    await redis_client.incr(rate_key)
    await redis_client.expire(rate_key, 60)  # Expire after 1 minute


@router.post("/generate", response_model=GenerationResponse)
async def generate_text(
    request: GenerationRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Generate text using the specified model."""
    global request_count, model_usage
    
    # Check rate limit
    await check_rate_limit(http_request, api_key)
    
    start_time = time.time()
    request_count += 1
    
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        # Use specified model or current model
        model_name = request.model or model_manager.get_current_model()
        if not model_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No model specified and no current model loaded"
            )
        
        # Create generation config
        config = GenerationConfig(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            repetition_penalty=request.repetition_penalty,
            do_sample=True,
        )
        
        # Generate response
        result = await model_manager.generate(request.prompt, model_name, config)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            )
        
        # Update model usage
        model_usage[model_name] = model_usage.get(model_name, 0) + 1
        
        # Log request
        log_request(
            logger,
            http_request.method,
            str(http_request.url),
            200,
            time.time() - start_time,
            http_request.client.host if http_request.client else "unknown",
            http_request.headers.get("user-agent", "unknown"),
            api_key[:8] + "..."
        )
        
        return GenerationResponse(
            response=result.response,
            model=result.model_name,
            tokens_used=result.tokens_used,
            processing_time=result.processing_time,
            timestamp=result.timestamp,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in generate endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Chat with context using the specified model."""
    global request_count, model_usage
    
    # Check rate limit
    await check_rate_limit(http_request, api_key)
    
    start_time = time.time()
    request_count += 1
    
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        # Use specified model or current model
        model_name = request.model or model_manager.get_current_model()
        if not model_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No model specified and no current model loaded"
            )
        
        # Create generation config
        config = GenerationConfig(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            repetition_penalty=request.repetition_penalty,
            do_sample=True,
        )
        
        # Convert messages to format expected by model manager
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Generate response
        result = await model_manager.chat(messages, model_name, config)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate chat response"
            )
        
        # Update model usage
        model_usage[model_name] = model_usage.get(model_name, 0) + 1
        
        # Log request
        log_request(
            logger,
            http_request.method,
            str(http_request.url),
            200,
            time.time() - start_time,
            http_request.client.host if http_request.client else "unknown",
            http_request.headers.get("user-agent", "unknown"),
            api_key[:8] + "..."
        )
        
        return ChatResponse(
            response=result.response,
            model=result.model_name,
            tokens_used=result.tokens_used,
            processing_time=result.processing_time,
            timestamp=result.timestamp,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in chat endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """List all available models."""
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        # Get model information
        models = []
        for model_name in model_manager.get_available_models():
            model_info = model_manager.get_model_info(model_name)
            if model_info:
                models.append(ModelInfo(
                    name=model_info.name,
                    type=model_info.type,
                    path=model_info.path,
                    format=model_info.format,
                    device=model_info.device,
                    quantization=model_info.quantization,
                    context_length=model_info.context_length,
                    max_memory=model_info.max_memory,
                    threads=model_info.threads,
                    loaded=model_info.loaded,
                    load_time=model_info.load_time,
                    memory_usage=model_info.memory_usage,
                ))
        
        return ModelListResponse(
            models=models,
            current_model=model_manager.get_current_model(),
            total_models=len(models),
        )
        
    except Exception as e:
        logger.error("Error in list_models endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/models/load", response_model=ModelLoadResponse)
async def load_model(
    request: ModelLoadRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Load a specific model."""
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        # Load the model
        success = await model_manager.load_model(request.model_name)
        
        if success:
            model_info = model_manager.get_model_info(request.model_name)
            return ModelLoadResponse(
                success=True,
                model_name=request.model_name,
                load_time=model_info.load_time if model_info else None,
                memory_usage=model_info.memory_usage if model_info else None,
                message="Model loaded successfully"
            )
        else:
            return ModelLoadResponse(
                success=False,
                model_name=request.model_name,
                message="Failed to load model"
            )
        
    except Exception as e:
        logger.error("Error in load_model endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/models/unload", response_model=ModelUnloadResponse)
async def unload_model(
    request: ModelUnloadRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Unload a specific model."""
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        # Unload the model
        success = await model_manager.unload_model(request.model_name)
        
        return ModelUnloadResponse(
            success=success,
            model_name=request.model_name,
            message="Model unloaded successfully" if success else "Failed to unload model"
        )
        
    except Exception as e:
        logger.error("Error in unload_model endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/models/status", response_model=ModelStatusResponse)
async def get_model_status(
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Get current model status."""
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        return ModelStatusResponse(
            current_model=model_manager.get_current_model(),
            loaded_models=model_manager.get_loaded_models(),
            available_models=model_manager.get_available_models(),
            memory_usage=psutil.virtual_memory().used / (1024 ** 3),  # GB
        )
        
    except Exception as e:
        logger.error("Error in get_model_status endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        # Get Redis client
        redis_client = await get_redis_client()
        
        # Check Redis health
        redis_health = await redis_client.health_check()
        
        # Get model manager health
        model_manager_health = await model_manager.health_check()
        
        # Calculate uptime
        uptime = time.time() - start_time
        
        return HealthResponse(
            status="healthy" if redis_health and model_manager_health["status"] == "healthy" else "unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            uptime=uptime,
            model_manager=model_manager_health,
            redis={"status": "healthy" if redis_health else "unhealthy"},
        )
        
    except Exception as e:
        logger.error("Error in health_check endpoint", error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            uptime=time.time() - start_time,
            model_manager={"status": "unhealthy", "error": str(e)},
            redis={"status": "unhealthy", "error": str(e)},
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Get system metrics."""
    try:
        # Calculate metrics
        uptime = time.time() - start_time
        requests_per_minute = (request_count / uptime) * 60 if uptime > 0 else 0
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        return MetricsResponse(
            requests_total=request_count,
            requests_per_minute=requests_per_minute,
            average_response_time=0.0,  # Would need to track this
            error_rate=0.0,  # Would need to track this
            memory_usage=memory.used / (1024 ** 3),  # GB
            cpu_usage=cpu,
            active_connections=0,  # Would need to track this
            model_usage=model_usage,
        )
        
    except Exception as e:
        logger.error("Error in get_metrics endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/webhooks/telegram")
async def telegram_webhook(
    request: WebhookRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Telegram webhook endpoint."""
    try:
        # Process webhook
        logger.info("Received Telegram webhook", event_type=request.event_type)
        
        return WebhookResponse(
            success=True,
            message="Webhook processed successfully",
            processed_at=datetime.utcnow().isoformat(),
        )
        
    except Exception as e:
        logger.error("Error in telegram_webhook endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/batch", response_model=BatchResponse)
async def batch_generate(
    request: BatchRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Batch text generation."""
    global request_count, model_usage
    
    # Check rate limit
    await check_rate_limit(http_request, api_key)
    
    start_time = time.time()
    request_count += 1
    
    try:
        # Get model manager
        model_manager = await get_model_manager()
        
        responses = []
        successful_requests = 0
        failed_requests = 0
        
        # Process requests
        for gen_request in request.requests:
            try:
                # Use specified model or current model
                model_name = gen_request.model or model_manager.get_current_model()
                if not model_name:
                    failed_requests += 1
                    continue
                
                # Create generation config
                config = GenerationConfig(
                    max_tokens=gen_request.max_tokens,
                    temperature=gen_request.temperature,
                    top_p=gen_request.top_p,
                    top_k=gen_request.top_k,
                    repetition_penalty=gen_request.repetition_penalty,
                    do_sample=True,
                )
                
                # Generate response
                result = await model_manager.generate(gen_request.prompt, model_name, config)
                if result:
                    responses.append(GenerationResponse(
                        response=result.response,
                        model=result.model_name,
                        tokens_used=result.tokens_used,
                        processing_time=result.processing_time,
                        timestamp=result.timestamp,
                    ))
                    successful_requests += 1
                    
                    # Update model usage
                    model_usage[model_name] = model_usage.get(model_name, 0) + 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                logger.error("Error processing batch request", error=str(e))
                failed_requests += 1
        
        return BatchResponse(
            responses=responses,
            total_processing_time=time.time() - start_time,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
        )
        
    except Exception as e:
        logger.error("Error in batch_generate endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/sessions", response_model=SessionResponse)
async def manage_session(
    request: SessionRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Manage user sessions."""
    try:
        # Get Redis client
        redis_client = await get_redis_client()
        
        session_id = request.session_id or str(uuid.uuid4())
        
        if request.action == "create":
            await redis_client.set_session_data(session_id, request.data or {})
            message = "Session created successfully"
        elif request.action == "get":
            data = await redis_client.get_session_data(session_id)
            return SessionResponse(
                session_id=session_id,
                success=True,
                data=data,
                message="Session retrieved successfully"
            )
        elif request.action == "update":
            await redis_client.set_session_data(session_id, request.data or {})
            message = "Session updated successfully"
        elif request.action == "delete":
            await redis_client.delete_session(session_id)
            message = "Session deleted successfully"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action"
            )
        
        return SessionResponse(
            session_id=session_id,
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in manage_session endpoint", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Core System API",
        "version": "1.0.0",
        "description": "Modular AI Core System for Model Management and API Services",
        "endpoints": {
            "generate": "/api/v1/generate",
            "chat": "/api/v1/chat",
            "models": "/api/v1/models",
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics",
        },
        "documentation": "/docs",
    } 