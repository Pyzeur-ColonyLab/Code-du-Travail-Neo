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

router = APIRouter(prefix="/api/v1", tags=["AI Core System"])


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    model: str = "code-du-travail-mistral"
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
        # Read models configuration
        config_path = "config/models.json"
        if not os.path.exists(config_path):
            # Return default models if config doesn't exist
            models = [
                ModelInfo(
                    name="code-du-travail-mistral",
                    type="transformers",
                    path="Pyzeur/Code-du-Travail-mistral-finetune",
                    format="safetensor",
                    device="auto",
                    quantization="4bit",
                    context_length=4096,
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=512,
                    loaded=False
                ),
                ModelInfo(
                    name="mistral-7b-instruct",
                    type="transformers",
                    path="mistralai/Mistral-7B-Instruct-v0.2",
                    format="safetensor",
                    device="auto",
                    quantization="4bit",
                    context_length=4096,
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=512,
                    loaded=False
                )
            ]
            return ModelListResponse(
                models=models,
                default_model="code-du-travail-mistral",
                total_models=len(models)
            )
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
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
                loaded=False  # For now, always false
            ))
        
        return ModelListResponse(
            models=models,
            default_model=config.get("default_model", "code-du-travail-mistral"),
            total_models=len(models)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load models: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for AI model interaction."""
    start_time = time.time()
    
    try:
        # For now, return a simple response
        # Later this will integrate with the actual AI model
        response_text = f"AI Model '{request.model}' received: {request.message}"
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            model=request.model,
            processing_time=processing_time,
            tokens_used=len(request.message.split())  # Simple token estimation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model_info(model_name: str):
    """Get information about a specific model."""
    try:
        # Read models configuration
        config_path = "config/models.json"
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="Model configuration not found")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
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
            loaded=False  # For now, always false
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.post("/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a specific model."""
    try:
        # For now, just return success
        # Later this will actually load the model
        return {
            "message": f"Model '{model_name}' load request received",
            "model": model_name,
            "status": "pending"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.post("/models/{model_name}/unload")
async def unload_model(model_name: str):
    """Unload a specific model."""
    try:
        # For now, just return success
        # Later this will actually unload the model
        return {
            "message": f"Model '{model_name}' unload request received",
            "model": model_name,
            "status": "pending"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unload model: {str(e)}")


@router.get("/status")
async def get_status():
    """Get system status."""
    return {
        "status": "running",
        "service": "ai-core-system",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoints": {
            "health": "/api/v1/health",
            "models": "/api/v1/models",
            "chat": "/api/v1/chat",
            "status": "/api/v1/status"
        }
    } 