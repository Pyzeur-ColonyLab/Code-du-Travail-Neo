# Main AI Core System

A modular AI core system that serves as the central API for running various AI models (GGUF, SafeTensor, ONNX, LoRA) and can be easily integrated with different services (Telegram, Email, Web Interface).

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Main AI Core   │    │  Telegram Bot   │    │   Mail Service  │
│     System      │    │    Service      │    │                 │
│                 │    │                 │    │                 │
│ • API Server    │    │ • Bot Handler   │    │ • Email Monitor │
│ • Model Manager │    │ • Session Mgmt  │    │ • SMTP/IMAP     │
│ • Redis Cache   │    │ • Rate Limiting │    │ • Templates     │
│ • Health Check  │    │ • Webhook       │    │ • Queue Mgmt    │
│ • Metrics       │    │ • Commands      │    │ • Spam Filter   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Load Balancer │
                    │   (Nginx)       │
                    │                 │
                    │ • SSL/TLS       │
                    │ • Rate Limiting │
                    │ • Caching       │
                    │ • Health Check  │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Redis 6.0+
- Docker (optional)
- 16GB+ RAM (for model loading)
- 100GB+ SSD storage

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ai-core-system.git
   cd ai-core-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start Redis**
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

5. **Run the application**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t ai-core-system .
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## 📋 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/generate` | Generate AI responses |
| `POST` | `/api/v1/chat` | Chat with context |
| `GET` | `/api/v1/models` | List available models |
| `POST` | `/api/v1/models/load` | Load specific model |
| `POST` | `/api/v1/models/unload` | Unload model |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/metrics` | System metrics |

### Authentication

All API endpoints require authentication via API key header:
```
X-API-Key: your-api-key
```

### Example Usage

```bash
# Generate text
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, how are you?",
    "max_tokens": 100,
    "temperature": 0.7
  }'

# Chat with context
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi there!"},
      {"role": "user", "content": "How are you?"}
    ],
    "max_tokens": 100
  }'

# List models
curl -X GET "http://localhost:8000/api/v1/models" \
  -H "X-API-Key: your-api-key"
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0

# Model Configuration
DEFAULT_MODEL=mistral-7b-instruct
MODEL_CACHE_DIR=/app/cache

# Security
API_KEYS=["your-api-key-1","your-api-key-2"]
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Model Configuration

Models are configured in `config/models.json`:

```json
{
  "models": {
    "mistral-7b-instruct": {
      "type": "gguf",
      "path": "/app/models/mistral-7b-instruct.gguf",
      "context_length": 4096,
      "temperature": 0.7,
      "top_p": 0.9,
      "top_k": 40,
      "repeat_penalty": 1.1
    },
    "llama-2-7b-chat": {
      "type": "gguf",
      "path": "/app/models/llama-2-7b-chat.gguf",
      "context_length": 4096,
      "temperature": 0.7,
      "top_p": 0.9,
      "top_k": 40,
      "repeat_penalty": 1.1
    }
  }
}
```

## 📊 Monitoring & Metrics

### Health Checks

- **Endpoint**: `GET /api/v1/health`
- **Response**: JSON with system status
- **Checks**: Redis connection, model status, memory usage

### Metrics

- **Endpoint**: `GET /api/v1/metrics`
- **Format**: Prometheus metrics
- **Metrics**: Request count, response time, model usage, memory usage

### Logging

Structured JSON logging with configurable levels:
- Request/response logging
- Model operation logging
- Security event logging
- Performance metrics logging

## 🔒 Security

### Authentication
- API key-based authentication
- JWT tokens for session management
- Rate limiting per API key

### Input Validation
- Prompt length limits
- Content sanitization
- Malicious input detection

### Network Security
- HTTPS/TLS encryption
- CORS configuration
- IP whitelisting (optional)

## 🚀 Performance

### Optimization Features
- **Model Caching**: Cache loaded models in memory
- **Response Caching**: Cache API responses in Redis
- **Connection Pooling**: Efficient database connections
- **Async Processing**: Non-blocking operations
- **Model Quantization**: Memory-efficient model loading

### Scaling
- **Horizontal Scaling**: Multiple instances behind load balancer
- **Vertical Scaling**: Increase server resources
- **Model Distribution**: Load models across multiple servers

## 🔄 Integration

### Telegram Service
```python
# Example integration
import httpx

async def send_to_telegram(message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://telegram.cryptomaltese.com/api/v1/send",
            headers={"X-API-Key": "your-telegram-api-key"},
            json={"message": message}
        )
        return response.json()
```

### Mail Service
```python
# Example integration
async def process_email(email_content: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://mail.cryptomaltese.com/api/v1/process",
            headers={"X-API-Key": "your-mail-api-key"},
            json={"content": email_content}
        )
        return response.json()
```

## 🐳 Docker Deployment

### Production Deployment

1. **Build production image**
   ```bash
   docker build -t ai-core-system:latest .
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Monitor deployment**
   ```bash
   docker-compose logs -f ai-core-system
   ```

### Docker Compose Services

```yaml
services:
  ai-core-system:
    image: ai-core-system:latest
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - nginx

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## 🔧 Development

### Code Structure

```
ai-core-system/
├── app/
│   ├── api/           # API endpoints and routes
│   ├── core/          # Configuration and logging
│   ├── models/        # Model management
│   └── utils/         # Utility functions
├── config/            # Configuration files
├── tests/             # Test suite
├── scripts/           # Deployment scripts
├── nginx/             # Nginx configuration
├── docker-compose.yml # Docker services
├── Dockerfile         # Container definition
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/

# Sort imports
isort app/
```

## 📈 Monitoring & Alerting

### Prometheus Metrics

Available metrics:
- `ai_api_requests_total`: Total API requests
- `ai_api_request_duration_seconds`: Request duration
- `ai_model_loading_duration_seconds`: Model loading time
- `ai_model_memory_usage_bytes`: Model memory usage
- `ai_redis_connections`: Redis connection count

### Grafana Dashboards

Pre-configured dashboards for:
- API performance monitoring
- Model usage statistics
- System resource utilization
- Error rate tracking

### Alerting

Configured alerts for:
- High error rates
- Model loading failures
- Memory usage thresholds
- Redis connection issues

## 🔄 Backup & Recovery

### Automated Backups

- **Schedule**: Daily at 2 AM
- **Retention**: 30 days
- **Compression**: Enabled
- **Encryption**: Enabled

### Recovery Procedures

1. **Stop services**
   ```bash
   docker-compose down
   ```

2. **Restore from backup**
   ```bash
   ./scripts/restore.sh /path/to/backup
   ```

3. **Restart services**
   ```bash
   docker-compose up -d
   ```

## 🌐 Network Configuration

### DNS Setup

```dns
# Main AI API
ai-api.cryptomaltese.com.      IN  A       YOUR_SERVER_IP

# Health check
health.ai-api.cryptomaltese.com. IN  A       YOUR_SERVER_IP
```

### SSL/TLS

- **Certificate**: Let's Encrypt (automatic)
- **Renewal**: Automatic via certbot
- **HSTS**: Enabled
- **Cipher Suite**: Modern TLS 1.3

## 🔧 Troubleshooting

### Common Issues

1. **Model Loading Failures**
   - Check model file paths
   - Verify sufficient memory
   - Check model format compatibility

2. **Redis Connection Issues**
   - Verify Redis is running
   - Check connection URL
   - Test network connectivity

3. **High Memory Usage**
   - Monitor model memory usage
   - Consider model quantization
   - Implement model unloading

4. **Slow Response Times**
   - Check Redis performance
   - Monitor model loading times
   - Review rate limiting settings

### Debug Mode

Enable debug mode for detailed logging:
```bash
DEBUG=true LOG_LEVEL=DEBUG python -m uvicorn app.main:app
```

### Log Analysis

```bash
# View recent logs
tail -f /app/logs/ai-api.log

# Search for errors
grep "ERROR" /app/logs/ai-api.log

# Monitor request patterns
grep "HTTP request" /app/logs/ai-api.log
```

## 📚 Documentation

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### Architecture Documentation

- [System Architecture](docs/architecture.md)
- [API Design](docs/api-design.md)
- [Model Management](docs/model-management.md)
- [Security Guide](docs/security.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write comprehensive tests
- Update documentation
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check the docs folder
- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub discussions
- **Email**: support@cryptomaltese.com

### Community

- **Discord**: Join our Discord server
- **Telegram**: Follow our Telegram channel
- **Blog**: Read our technical blog

## 🔄 Changelog

### Version 1.0.0 (2024-01-01)

- Initial release
- Support for GGUF, SafeTensor, ONNX models
- RESTful API with authentication
- Redis caching layer
- Health monitoring and metrics
- Docker deployment support
- Comprehensive documentation

---

**Built with ❤️ by the Code du Travail Neo Team** 