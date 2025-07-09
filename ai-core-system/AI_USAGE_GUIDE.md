# AI Core System - Usage Guide

## 🚀 Overview

Your AI Core System is now fully functional with real AI model inference capabilities! The system supports multiple AI models with automatic loading, quantization, and caching.

## 📋 Available Models

The system is configured with three models optimized for CPU-only servers:

1. **`tiny-llama`** (Default) - TinyLlama 1.1B Chat model
   - Very lightweight and fast
   - Perfect for CPU-only servers
   - Memory usage: ~2GB
   - Best choice for testing and simple tasks

2. **`phi-2`** - Microsoft's Phi-2 model (2.7B parameters)
   - Good balance of quality and speed
   - Works well on CPU
   - Memory usage: ~4GB
   - Good for general tasks

3. **`mistral-7b-instruct`** - Mistral 7B Instruct model
   - Highest quality responses
   - More resource intensive
   - Memory usage: ~8GB
   - Best for complex tasks (if you have enough RAM)

## 🔧 API Endpoints

### 1. Health Check
```bash
GET /api/v1/health
```

### 2. List Available Models
```bash
GET /api/v1/models
```

### 3. Load a Model
```bash
POST /api/v1/models/{model_name}/load
```

### 4. Unload a Model
```bash
POST /api/v1/models/{model_name}/unload
```

### 5. Chat with AI
```bash
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Your question here",
  "model": "phi-2",
  "temperature": 0.7,
  "max_tokens": 512,
  "top_p": 0.9
}
```

### 6. Get System Status
```bash
GET /api/v1/status
```

## 🎯 How to Use

### Step 1: Check Available Models
Visit: https://cryptomaltese.com/docs

1. Click on `GET /api/v1/models`
2. Click "Try it out"
3. Click "Execute"

You'll see all available models and their loading status.

### Step 2: Load a Model
1. Click on `POST /api/v1/models/{model_name}/load`
2. Click "Try it out"
3. Enter the model name (e.g., `phi-2`)
4. Click "Execute"

**Note:** The first time you load a model, it will download from Hugging Face (this may take several minutes depending on your internet speed and the model size).

### Step 3: Chat with the AI
1. Click on `POST /api/v1/chat`
2. Click "Try it out"
3. Enter your request:
```json
{
  "message": "Hello! Can you explain what artificial intelligence is?",
  "model": "tiny-llama",
  "temperature": 0.7,
  "max_tokens": 256
}
```
4. Click "Execute"

## 🧪 Testing Your Setup

### Using the Test Script
```bash
# On your local machine
python test_ai_api.py
```

### Manual Testing with curl
```bash
# List models
curl -X GET "https://cryptomaltese.com/api/v1/models"

# Load a model
curl -X POST "https://cryptomaltese.com/api/v1/models/tiny-llama/load"

# Chat with AI
curl -X POST "https://cryptomaltese.com/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?",
    "model": "tiny-llama",
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

## ⚙️ Configuration

### Model Settings
Edit `config/models.json` to modify model configurations:

```json
{
  "models": {
    "tiny-llama": {
      "type": "transformers",
      "path": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
      "device": "cpu",
      "quantization": "none",
      "max_memory": "2GB",
      "temperature": 0.7,
      "max_tokens": 512
    }
  }
}
```
```

### Environment Variables
Key environment variables in your `.env` file:

```bash
# Model Configuration
MODEL_CACHE_DIR=/app/cache
DEFAULT_MODEL=tiny-llama
MODEL_LOAD_TIMEOUT=300

# Performance
MAX_MODEL_MEMORY_GB=16
MODEL_QUANTIZATION=none
```
```

## 🔍 Troubleshooting

### Model Loading Issues
1. **Out of Memory**: Try a smaller model like `tiny-llama`
2. **Download Timeout**: Check your internet connection
3. **Permission Errors**: Ensure the cache directory is writable

### Performance Optimization
1. **Use CPU-optimized models** (already configured)
2. **Load smaller models** for faster responses
3. **Unload unused models** to free memory
4. **Start with tiny-llama** for testing

### Common Error Messages
- `"Model not found"`: Check the model name in `/api/v1/models`
- `"Failed to load model"`: Check server logs for details
- `"Out of memory"`: Try unloading other models first

## 📊 Monitoring

### Check System Status
```bash
GET /api/v1/status
```

This shows:
- Currently loaded models
- Device (CPU/GPU)
- System status

### View Logs
```bash
# On your server
sudo docker compose logs ai-api
```

## 🚀 Next Steps

1. **Test with different models** to find the best fit for your use case
2. **Adjust model parameters** (temperature, max_tokens) for different response styles
3. **Monitor performance** and adjust configurations as needed
4. **Consider adding more models** to your configuration

## 📞 Support

If you encounter issues:
1. Check the server logs
2. Verify model configurations
3. Test with the provided test script
4. Check system resources (memory, disk space)

---

**Happy AI Chatting! 🤖✨** 