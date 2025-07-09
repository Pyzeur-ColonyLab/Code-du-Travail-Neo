"""
Pydantic models for API request/response schemas.

This module defines the data models used for API communication,
including request validation and response serialization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")


class GenerationRequest(BaseModel):
    """Text generation request model."""
    model: Optional[str] = Field(None, description="Model name to use")
    prompt: str = Field(..., description="Input prompt for generation")
    max_tokens: int = Field(512, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: int = Field(50, ge=1, le=100, description="Top-k sampling parameter")
    repetition_penalty: float = Field(1.1, ge=1.0, le=2.0, description="Repetition penalty")
    stream: bool = Field(False, description="Whether to stream the response")
    
    @validator('prompt')
    def validate_prompt_length(cls, v):
        """Validate prompt length."""
        if len(v) > 4096:
            raise ValueError('Prompt too long (max 4096 characters)')
        return v


class ChatRequest(BaseModel):
    """Chat request model."""
    model: Optional[str] = Field(None, description="Model name to use")
    messages: List[Message] = Field(..., description="Chat messages")
    max_tokens: int = Field(512, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: int = Field(50, ge=1, le=100, description="Top-k sampling parameter")
    repetition_penalty: float = Field(1.1, ge=1.0, le=2.0, description="Repetition penalty")
    stream: bool = Field(False, description="Whether to stream the response")
    
    @validator('messages')
    def validate_messages(cls, v):
        """Validate messages."""
        if not v:
            raise ValueError('At least one message is required')
        
        # Check total content length
        total_length = sum(len(msg.content) for msg in v)
        if total_length > 4096:
            raise ValueError('Total message content too long (max 4096 characters)')
        
        return v


class GenerationResponse(BaseModel):
    """Text generation response model."""
    response: str = Field(..., description="Generated text response")
    model: str = Field(..., description="Model used for generation")
    tokens_used: int = Field(..., description="Number of tokens used")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: str = Field(..., description="ISO timestamp of generation")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Generated chat response")
    model: str = Field(..., description="Model used for generation")
    tokens_used: int = Field(..., description="Number of tokens used")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: str = Field(..., description="ISO timestamp of generation")


class ModelInfo(BaseModel):
    """Model information model."""
    name: str = Field(..., description="Model name")
    type: str = Field(..., description="Model type (transformers, gguf, onnx)")
    path: str = Field(..., description="Model path")
    format: str = Field(..., description="Model format")
    device: str = Field(..., description="Device used for inference")
    quantization: str = Field(..., description="Quantization method")
    context_length: int = Field(..., description="Context length")
    max_memory: str = Field(..., description="Maximum memory usage")
    threads: int = Field(..., description="Number of threads")
    loaded: bool = Field(..., description="Whether model is loaded")
    load_time: Optional[float] = Field(None, description="Model load time in seconds")
    memory_usage: Optional[float] = Field(None, description="Current memory usage in GB")


class ModelListResponse(BaseModel):
    """Model list response model."""
    models: List[ModelInfo] = Field(..., description="List of available models")
    current_model: Optional[str] = Field(None, description="Currently active model")
    total_models: int = Field(..., description="Total number of models")


class ModelLoadRequest(BaseModel):
    """Model load request model."""
    model_name: str = Field(..., description="Name of the model to load")


class ModelLoadResponse(BaseModel):
    """Model load response model."""
    success: bool = Field(..., description="Whether loading was successful")
    model_name: str = Field(..., description="Name of the loaded model")
    load_time: Optional[float] = Field(None, description="Load time in seconds")
    memory_usage: Optional[float] = Field(None, description="Memory usage in GB")
    message: str = Field(..., description="Status message")


class ModelUnloadRequest(BaseModel):
    """Model unload request model."""
    model_name: str = Field(..., description="Name of the model to unload")


class ModelUnloadResponse(BaseModel):
    """Model unload response model."""
    success: bool = Field(..., description="Whether unloading was successful")
    model_name: str = Field(..., description="Name of the unloaded model")
    message: str = Field(..., description="Status message")


class ModelStatusResponse(BaseModel):
    """Model status response model."""
    current_model: Optional[str] = Field(None, description="Currently active model")
    loaded_models: List[str] = Field(..., description="List of loaded models")
    available_models: List[str] = Field(..., description="List of available models")
    memory_usage: float = Field(..., description="Current memory usage in GB")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Service uptime in seconds")
    model_manager: Dict[str, Any] = Field(..., description="Model manager health")
    redis: Dict[str, Any] = Field(..., description="Redis health")


class MetricsResponse(BaseModel):
    """Metrics response model."""
    requests_total: int = Field(..., description="Total number of requests")
    requests_per_minute: float = Field(..., description="Requests per minute")
    average_response_time: float = Field(..., description="Average response time in seconds")
    error_rate: float = Field(..., description="Error rate percentage")
    memory_usage: float = Field(..., description="Memory usage in GB")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    active_connections: int = Field(..., description="Active connections")
    model_usage: Dict[str, int] = Field(..., description="Model usage statistics")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class RateLimitResponse(BaseModel):
    """Rate limit response model."""
    error: str = Field(..., description="Rate limit error message")
    retry_after: int = Field(..., description="Seconds to wait before retrying")
    limit: int = Field(..., description="Rate limit (requests per minute)")
    remaining: int = Field(..., description="Remaining requests in current window")


class WebhookRequest(BaseModel):
    """Webhook request model for external integrations."""
    event_type: str = Field(..., description="Type of webhook event")
    data: Dict[str, Any] = Field(..., description="Webhook data")
    timestamp: str = Field(..., description="Webhook timestamp")
    signature: Optional[str] = Field(None, description="Webhook signature for verification")


class WebhookResponse(BaseModel):
    """Webhook response model."""
    success: bool = Field(..., description="Whether webhook was processed successfully")
    message: str = Field(..., description="Status message")
    processed_at: str = Field(..., description="Processing timestamp")


class StreamChunk(BaseModel):
    """Streaming response chunk model."""
    chunk: str = Field(..., description="Text chunk")
    done: bool = Field(..., description="Whether streaming is complete")
    model: str = Field(..., description="Model used for generation")
    tokens_used: Optional[int] = Field(None, description="Tokens used so far")


class BatchRequest(BaseModel):
    """Batch processing request model."""
    requests: List[GenerationRequest] = Field(..., description="List of generation requests")
    max_concurrent: int = Field(10, ge=1, le=50, description="Maximum concurrent requests")
    
    @validator('requests')
    def validate_requests(cls, v):
        """Validate batch requests."""
        if not v:
            raise ValueError('At least one request is required')
        if len(v) > 100:
            raise ValueError('Too many requests in batch (max 100)')
        return v


class BatchResponse(BaseModel):
    """Batch processing response model."""
    responses: List[GenerationResponse] = Field(..., description="List of generation responses")
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    successful_requests: int = Field(..., description="Number of successful requests")
    failed_requests: int = Field(..., description="Number of failed requests")


class SessionRequest(BaseModel):
    """Session management request model."""
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    action: str = Field(..., description="Session action (create, get, update, delete)")
    data: Optional[Dict[str, Any]] = Field(None, description="Session data")


class SessionResponse(BaseModel):
    """Session management response model."""
    session_id: str = Field(..., description="Session ID")
    success: bool = Field(..., description="Whether operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Session data")
    expires_at: Optional[str] = Field(None, description="Session expiration timestamp")
    message: str = Field(..., description="Status message") 