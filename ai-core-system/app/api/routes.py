"""
API routes for the AI Core System.

This module defines all the API endpoints for model management,
chat functionality, and system operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import json
import os
import logging

from ..core.model_manager import model_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["AI Core System"])


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    model: str = "tiny-llama"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    top_p: Optional[float] = 0.9


class ChatResponse(BaseModel):
    response: str
    model: str
    processing_time: float
    tokens_used: Optional[int] = None


class ModelInfo(BaseModel):
    name: str
    type: str
    path: str
    format: str
    device: str
    quantization: str
    context_length: int
    temperature: float
    top_p: float
    max_tokens: int
    loaded: bool


class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    default_model: str
    total_models: int


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    version: str


# API Endpoints
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="ai-core-system",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        version="1.0.0"
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """List all available models."""
    try:
        # Load model configurations
        config = model_manager.load_config()
        
        models = []
        for name, model_config in config.get("models", {}).items():
            models.append(ModelInfo(
                name=name,
                type=model_config.get("type", "transformers"),
                path=model_config.get("path", ""),
                format=model_config.get("format", "safetensor"),
                device=model_config.get("device", "auto"),
                quantization=model_config.get("quantization", "4bit"),
                context_length=model_config.get("context_length", 4096),
                temperature=model_config.get("temperature", 0.7),
                top_p=model_config.get("top_p", 0.9),
                max_tokens=model_config.get("max_tokens", 512),
                loaded=model_manager.is_model_loaded(name)
            ))
        
        return ModelListResponse(
            models=models,
            default_model=config.get("default_model", "mistral-7b-instruct"),
            total_models=len(models)
        )
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load models: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for AI model interaction."""
    try:
        logger.info(f"Chat request received for model '{request.model}': {request.message[:100]}...")
        
        # Generate response using the model manager
        result = model_manager.generate_response(
            model_name=request.model,
            prompt=request.message,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        logger.info(f"Generated response in {result['processing_time']:.2f}s with {result['tokens_used']} tokens")
        
        return ChatResponse(
            response=result["response"],
            model=result["model"],
            processing_time=result["processing_time"],
            tokens_used=result["tokens_used"]
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model_info(model_name: str):
    """Get information about a specific model."""
    try:
        # Load model configurations
        config = model_manager.load_config()
        
        if model_name not in config.get("models", {}):
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        
        model_config = config["models"][model_name]
        
        return ModelInfo(
            name=model_name,
            type=model_config.get("type", "transformers"),
            path=model_config.get("path", ""),
            format=model_config.get("format", "safetensor"),
            device=model_config.get("device", "auto"),
            quantization=model_config.get("quantization", "4bit"),
            context_length=model_config.get("context_length", 4096),
            temperature=model_config.get("temperature", 0.7),
            top_p=model_config.get("top_p", 0.9),
            max_tokens=model_config.get("max_tokens", 512),
            loaded=model_manager.is_model_loaded(model_name)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info for '{model_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.post("/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a specific model."""
    try:
        logger.info(f"Loading model '{model_name}'...")
        
        success = model_manager.load_model(model_name)
        
        if success:
            logger.info(f"Successfully loaded model '{model_name}'")
            return {
                "message": f"Model '{model_name}' loaded successfully",
                "model": model_name,
                "status": "loaded",
                "loaded_at": time.time()
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to load model '{model_name}'")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model '{model_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.post("/models/{model_name}/unload")
async def unload_model(model_name: str):
    """Unload a specific model."""
    try:
        logger.info(f"Unloading model '{model_name}'...")
        
        success = model_manager.unload_model(model_name)
        
        if success:
            logger.info(f"Successfully unloaded model '{model_name}'")
            return {
                "message": f"Model '{model_name}' unloaded successfully",
                "model": model_name,
                "status": "unloaded",
                "unloaded_at": time.time()
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to unload model '{model_name}'")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload model '{model_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unload model: {str(e)}")


@router.get("/status")
async def get_status():
    """Get system status."""
    try:
        # Get loaded models
        loaded_models = model_manager.get_loaded_models()
        
        return {
            "status": "running",
            "service": "ai-core-system",
            "version": "1.0.0",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "device": model_manager.device,
            "loaded_models": loaded_models,
            "total_loaded_models": len(loaded_models),
            "endpoints": {
                "health": "/api/v1/health",
                "models": "/api/v1/models",
                "chat": "/api/v1/chat",
                "status": "/api/v1/status"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}") 