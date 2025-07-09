# AI Core System

A modular AI Core System for Model Management and API Services.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM available
- Internet connection for model downloads

### Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pyzeur-ColonyLab/Code-du-Travail-Neo.git
   cd Code-du-Travail-Neo/ai-core-system
   ```

2. **Create environment file**
   ```bash
   cp env.example .env
   # Edit .env if needed
   ```

3. **Build and start services**
   ```bash
   sudo docker compose build
   sudo docker compose up -d
   ```

4. **Check status**
   ```bash
   sudo docker compose ps
   sudo docker compose logs -f ai-api
   ```

### Testing

Once the services are running, test the API:

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/api/v1/models

# Chat endpoint
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?", "model": "code-du-travail-mistral"}'
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Services

- **AI API**: Port 8000 (FastAPI application)
- **Redis**: Port 6379 (Caching and session management)
- **Nginx**: Port 8080 (Reverse proxy)

### Configuration

- Model configuration: `config/models.json`
- Environment variables: `.env`
- Nginx configuration: `nginx/nginx.conf`

### Logs

```bash
# View all logs
sudo docker compose logs

# View specific service logs
sudo docker compose logs -f ai-api
sudo docker compose logs -f redis
sudo docker compose logs -f nginx
```

### Stopping Services

```bash
sudo docker compose down
```

### Troubleshooting

1. **Port conflicts**: Change ports in `docker-compose.yml`
2. **Memory issues**: Ensure sufficient RAM (8GB+ recommended)
3. **Model loading**: Check logs for download progress
4. **Permission issues**: Use `sudo` with Docker commands

## Model Configuration

The system supports multiple AI models. Edit `config/models.json` to add or modify models:

```json
{
  "models": {
    "code-du-travail-mistral": {
      "type": "transformers",
      "path": "Pyzeur/Code-du-Travail-mistral-finetune",
      "format": "safetensor",
      "device": "auto",
      "quantization": "4bit",
      "max_memory": "8GB",
      "context_length": 4096,
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 512
    }
  },
  "default_model": "code-du-travail-mistral"
}
```

## Development

For development, you can run the application directly:

```bash
pip install -r requirements.txt
python main.py
```

## License

This project is licensed under the MIT License. 