"""
Model Manager for AI Core System.

This module handles loading, unloading, and inference with AI models
using the transformers library with support for quantization and caching.
"""

import os
import time
import json
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig,
    pipeline
)
# Add PEFT import
try:
    from peft import PeftModel
except ImportError:
    PeftModel = None

from app.models.model_factory import ModelFactory
from app.models.base_model import BaseModel

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages AI model loading, unloading, and inference."""
    
    def __init__(self, cache_dir: str = "/app/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.loaded_models: Dict[str, BaseModel] = {}
        self.model_configs: Dict[str, Dict] = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Get Hugging Face token from environment
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if self.hf_token:
            logger.info("Hugging Face token found - will use for model downloads")
        else:
            logger.warning("No Hugging Face token found - some models may not be accessible")
        
        logger.info(f"ModelManager initialized with device: {self.device}")
        logger.info(f"Cache directory: {self.cache_dir}")
    
    def load_config(self, config_path: str = "/app/config/models.json") -> Dict:
        """Load model configurations from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.model_configs = config.get("models", {})
            logger.info(f"Loaded {len(self.model_configs)} model configurations from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load model config from {config_path}: {e}")
            # Return default config
            return {
                "models": {
                    "mistral-7b-instruct": {
                        "type": "transformers",
                        "path": "mistralai/Mistral-7B-Instruct-v0.2",
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
                "default_model": "mistral-7b-instruct"
            }
    
    def load_model(self, model_name: str) -> bool:
        """Load a specific model into memory using the factory and config."""
        try:
            self.load_config()
            if model_name in self.loaded_models:
                logger.info(f"Model '{model_name}' is already loaded")
                return True
            if model_name not in self.model_configs:
                logger.error(f"Model '{model_name}' not found in configuration")
                return False
            config = self.model_configs[model_name]
            logger.info(f"Loading model '{model_name}' with config: {config}")
            model_type = config.get("type", "transformer")
            model_path = config["path"]
            model_instance = ModelFactory.create_model(model_type)
            model_instance.load_model(model_path)
            self.loaded_models[model_name] = model_instance
            logger.info(f"Successfully loaded model '{model_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to load model '{model_name}': {e}")
            return False
    
    def unload_model(self, model_name: str) -> bool:
        """Unload a specific model from memory."""
        try:
            if model_name not in self.loaded_models:
                logger.warning(f"Model '{model_name}' is not loaded")
                return True
            del self.loaded_models[model_name]
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info(f"Successfully unloaded model '{model_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to unload model '{model_name}': {e}")
            return False
    
    def generate_response(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """Generate a response using the specified model."""
        try:
            if model_name not in self.loaded_models:
                if not self.load_model(model_name):
                    raise Exception(f"Failed to load model '{model_name}'")
            model_instance = self.loaded_models[model_name]
            # For extensibility, pass parameters as needed
            result = model_instance.predict(prompt)
            return {
                "response": result.get("generated_text", ""),
                "model": model_name,
                "processing_time": None,  # Optionally add timing
                "tokens_used": None,      # Optionally add token count
            }
        except Exception as e:
            logger.error(f"Failed to generate response with model '{model_name}': {e}")
            raise Exception(f"Model inference failed: {e}")
    
    def get_loaded_models(self) -> List[str]:
        return list(self.loaded_models.keys())
    
    def is_model_loaded(self, model_name: str) -> bool:
        return model_name in self.loaded_models
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        if model_name in self.loaded_models:
            return self.loaded_models[model_name].get_model_info()
        return None


# Global model manager instance
model_manager = ModelManager() 