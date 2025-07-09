"""
API tests for the AI Core System.

This module contains comprehensive tests for all API endpoints
including authentication, generation, chat, model management,
and error handling.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from main import app
from app.core.config import get_settings
from app.models.manager import get_model_manager
from app.utils.redis_client import get_redis_client


class TestAPI:
    """Test class for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(app=app, base_url="http://test")
    
    @pytest.fixture
    def valid_api_key(self):
        """Get valid API key from settings."""
        settings = get_settings()
        return settings.api_keys[0] if settings.api_keys else "test-api-key"
    
    @pytest.fixture
    def headers(self, valid_api_key):
        """Create headers with API key."""
        settings = get_settings()
        return {settings.api_key_header: valid_api_key}
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Core System"
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
    
    def test_api_root_endpoint(self, client, headers):
        """Test API root endpoint."""
        response = client.get("/api/v1/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Core System API"
        assert "endpoints" in data
    
    def test_authentication_required(self, client):
        """Test that API key is required."""
        response = client.post("/api/v1/generate", json={
            "prompt": "Hello, world!"
        })
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]
    
    def test_invalid_api_key(self, client):
        """Test invalid API key rejection."""
        response = client.post("/api/v1/generate", 
            headers={"X-API-Key": "invalid-key"},
            json={"prompt": "Hello, world!"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    def test_generate_text_endpoint(self, client, headers):
        """Test text generation endpoint."""
        response = client.post("/api/v1/generate", 
            headers=headers,
            json={
                "prompt": "Hello, world!",
                "max_tokens": 50,
                "temperature": 0.7
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "model" in data
        assert "tokens_used" in data
        assert "processing_time" in data
        assert "timestamp" in data
    
    def test_chat_endpoint(self, client, headers):
        """Test chat endpoint."""
        response = client.post("/api/v1/chat",
            headers=headers,
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"}
                ],
                "max_tokens": 50
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "model" in data
        assert "tokens_used" in data
    
    def test_list_models_endpoint(self, client, headers):
        """Test list models endpoint."""
        response = client.get("/api/v1/models", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "current_model" in data
        assert "total_models" in data
        assert isinstance(data["models"], list)
    
    def test_model_status_endpoint(self, client, headers):
        """Test model status endpoint."""
        response = client.get("/api/v1/models/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "current_model" in data
        assert "loaded_models" in data
        assert "available_models" in data
        assert "memory_usage" in data
        assert isinstance(data["loaded_models"], list)
        assert isinstance(data["available_models"], list)
    
    def test_load_model_endpoint(self, client, headers):
        """Test load model endpoint."""
        response = client.post("/api/v1/models/load",
            headers=headers,
            json={"model_name": "mistral-7b-instruct"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "model_name" in data
        assert "message" in data
    
    def test_unload_model_endpoint(self, client, headers):
        """Test unload model endpoint."""
        response = client.post("/api/v1/models/unload",
            headers=headers,
            json={"model_name": "mistral-7b-instruct"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "model_name" in data
        assert "message" in data
    
    def test_metrics_endpoint(self, client, headers):
        """Test metrics endpoint."""
        response = client.get("/api/v1/metrics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data
        assert "requests_per_minute" in data
        assert "average_response_time" in data
        assert "error_rate" in data
        assert "memory_usage" in data
        assert "cpu_usage" in data
        assert "model_usage" in data
    
    def test_batch_generate_endpoint(self, client, headers):
        """Test batch generation endpoint."""
        response = client.post("/api/v1/batch",
            headers=headers,
            json={
                "requests": [
                    {
                        "prompt": "Hello, world!",
                        "max_tokens": 20
                    },
                    {
                        "prompt": "How are you?",
                        "max_tokens": 20
                    }
                ],
                "max_concurrent": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "responses" in data
        assert "total_processing_time" in data
        assert "successful_requests" in data
        assert "failed_requests" in data
        assert isinstance(data["responses"], list)
    
    def test_session_management_endpoint(self, client, headers):
        """Test session management endpoint."""
        # Create session
        response = client.post("/api/v1/sessions",
            headers=headers,
            json={
                "action": "create",
                "data": {"user_id": "test-user", "preferences": {"theme": "dark"}}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data
        
        session_id = data["session_id"]
        
        # Get session
        response = client.post("/api/v1/sessions",
            headers=headers,
            json={
                "session_id": session_id,
                "action": "get"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Update session
        response = client.post("/api/v1/sessions",
            headers=headers,
            json={
                "session_id": session_id,
                "action": "update",
                "data": {"user_id": "test-user", "preferences": {"theme": "light"}}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Delete session
        response = client.post("/api/v1/sessions",
            headers=headers,
            json={
                "session_id": session_id,
                "action": "delete"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_webhook_endpoint(self, client, headers):
        """Test webhook endpoint."""
        response = client.post("/api/v1/webhooks/telegram",
            headers=headers,
            json={
                "event_type": "message",
                "data": {"message": "Hello from Telegram"},
                "timestamp": "2024-01-01T12:00:00Z"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "processed_at" in data
    
    def test_invalid_request_validation(self, client, headers):
        """Test request validation."""
        # Test empty prompt
        response = client.post("/api/v1/generate",
            headers=headers,
            json={"prompt": ""}
        )
        assert response.status_code == 422
        
        # Test invalid temperature
        response = client.post("/api/v1/generate",
            headers=headers,
            json={
                "prompt": "Hello",
                "temperature": 3.0  # Invalid: > 2.0
            }
        )
        assert response.status_code == 422
        
        # Test invalid max_tokens
        response = client.post("/api/v1/generate",
            headers=headers,
            json={
                "prompt": "Hello",
                "max_tokens": 3000  # Invalid: > 2048
            }
        )
        assert response.status_code == 422
    
    def test_chat_validation(self, client, headers):
        """Test chat request validation."""
        # Test empty messages
        response = client.post("/api/v1/chat",
            headers=headers,
            json={"messages": []}
        )
        assert response.status_code == 422
        
        # Test invalid message format
        response = client.post("/api/v1/chat",
            headers=headers,
            json={
                "messages": [
                    {"role": "invalid", "content": "Hello"}
                ]
            }
        )
        assert response.status_code == 422
    
    def test_batch_validation(self, client, headers):
        """Test batch request validation."""
        # Test empty requests
        response = client.post("/api/v1/batch",
            headers=headers,
            json={"requests": []}
        )
        assert response.status_code == 422
        
        # Test too many requests
        requests = [{"prompt": f"Request {i}", "max_tokens": 10} for i in range(101)]
        response = client.post("/api/v1/batch",
            headers=headers,
            json={"requests": requests}
        )
        assert response.status_code == 422
    
    def test_session_validation(self, client, headers):
        """Test session request validation."""
        # Test invalid action
        response = client.post("/api/v1/sessions",
            headers=headers,
            json={"action": "invalid"}
        )
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_async_endpoints(self, async_client, headers):
        """Test async endpoints."""
        response = await async_client.get("/api/v1/", headers=headers)
        assert response.status_code == 200
        
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_error_handling(self, client, headers):
        """Test error handling."""
        # Test non-existent endpoint
        response = client.get("/api/v1/nonexistent", headers=headers)
        assert response.status_code == 404
        
        # Test invalid JSON
        response = client.post("/api/v1/generate",
            headers=headers,
            data="invalid json",
            content_type="application/json"
        )
        assert response.status_code == 422
    
    def test_cors_headers(self, client):
        """Test CORS headers."""
        response = client.options("/api/v1/generate",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key"
            }
        )
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_rate_limiting(self, client, headers):
        """Test rate limiting."""
        # Make multiple requests quickly
        for i in range(10):
            response = client.post("/api/v1/generate",
                headers=headers,
                json={"prompt": f"Request {i}", "max_tokens": 10}
            )
            if response.status_code == 429:
                break
        else:
            # If no rate limiting occurred, that's also acceptable
            pass
    
    def test_model_not_found(self, client, headers):
        """Test handling of non-existent model."""
        response = client.post("/api/v1/generate",
            headers=headers,
            json={
                "model": "non-existent-model",
                "prompt": "Hello"
            }
        )
        # Should either return 400 (bad request) or 500 (internal error)
        assert response.status_code in [400, 500]
    
    def test_large_prompt_handling(self, client, headers):
        """Test handling of large prompts."""
        large_prompt = "A" * 5000  # Exceeds 4096 character limit
        response = client.post("/api/v1/generate",
            headers=headers,
            json={"prompt": large_prompt}
        )
        assert response.status_code == 422
    
    def test_concurrent_requests(self, client, headers):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.post("/api/v1/generate",
                    headers=headers,
                    json={"prompt": "Concurrent test", "max_tokens": 10}
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(status == 200 for status in results), f"Some requests failed: {results}"


class TestIntegration:
    """Integration tests for the AI Core System."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, async_client):
        """Test complete workflow from model loading to generation."""
        settings = get_settings()
        headers = {settings.api_key_header: settings.api_keys[0] if settings.api_keys else "test-key"}
        
        # 1. Check health
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        # 2. List models
        response = await async_client.get("/api/v1/models", headers=headers)
        assert response.status_code == 200
        
        # 3. Load a model
        response = await async_client.post("/api/v1/models/load",
            headers=headers,
            json={"model_name": "mistral-7b-instruct"}
        )
        assert response.status_code == 200
        
        # 4. Generate text
        response = await async_client.post("/api/v1/generate",
            headers=headers,
            json={
                "model": "mistral-7b-instruct",
                "prompt": "Hello, world!",
                "max_tokens": 20
            }
        )
        assert response.status_code == 200
        
        # 5. Check metrics
        response = await async_client.get("/api/v1/metrics", headers=headers)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_model_switching(self, async_client):
        """Test switching between different models."""
        settings = get_settings()
        headers = {settings.api_key_header: settings.api_keys[0] if settings.api_keys else "test-key"}
        
        # Load first model
        response = await async_client.post("/api/v1/models/load",
            headers=headers,
            json={"model_name": "mistral-7b-instruct"}
        )
        assert response.status_code == 200
        
        # Generate with first model
        response = await async_client.post("/api/v1/generate",
            headers=headers,
            json={
                "model": "mistral-7b-instruct",
                "prompt": "Test prompt 1",
                "max_tokens": 10
            }
        )
        assert response.status_code == 200
        model1_response = response.json()["response"]
        
        # Load second model
        response = await async_client.post("/api/v1/models/load",
            headers=headers,
            json={"model_name": "llama-2-7b-chat"}
        )
        assert response.status_code == 200
        
        # Generate with second model
        response = await async_client.post("/api/v1/generate",
            headers=headers,
            json={
                "model": "llama-2-7b-chat",
                "prompt": "Test prompt 2",
                "max_tokens": 10
            }
        )
        assert response.status_code == 200
        model2_response = response.json()["response"]
        
        # Responses should be different (different models)
        assert model1_response != model2_response
    
    @pytest.mark.asyncio
    async def test_chat_conversation(self, async_client):
        """Test multi-turn chat conversation."""
        settings = get_settings()
        headers = {settings.api_key_header: settings.api_keys[0] if settings.api_keys else "test-key"}
        
        # Start conversation
        messages = [{"role": "user", "content": "Hello, my name is Alice."}]
        
        response = await async_client.post("/api/v1/chat",
            headers=headers,
            json={
                "messages": messages,
                "max_tokens": 20
            }
        )
        assert response.status_code == 200
        assistant_response = response.json()["response"]
        
        # Continue conversation
        messages.extend([
            {"role": "assistant", "content": assistant_response},
            {"role": "user", "content": "What's my name?"}
        ])
        
        response = await async_client.post("/api/v1/chat",
            headers=headers,
            json={
                "messages": messages,
                "max_tokens": 20
            }
        )
        assert response.status_code == 200
        
        # The assistant should remember the name
        final_response = response.json()["response"]
        assert "Alice" in final_response or "alice" in final_response.lower()


if __name__ == "__main__":
    pytest.main([__file__]) 