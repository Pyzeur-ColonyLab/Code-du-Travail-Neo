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

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages AI model loading, unloading, and inference."""
    
    def __init__(self, cache_dir: str = "/app/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.loaded_models: Dict[str, Any] = {}
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
        """Load a specific model into memory."""
        try:
            if model_name in self.loaded_models:
                logger.info(f"Model '{model_name}' is already loaded")
                return True
            
            if model_name not in self.model_configs:
                logger.error(f"Model '{model_name}' not found in configuration")
                return False
            
            config = self.model_configs[model_name]
            logger.info(f"Loading model '{model_name}' with config: {config}")
            
            quantization_config = None
            if config.get("quantization") == "4bit" and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            elif config.get("quantization") == "4bit" and self.device == "cpu":
                logger.warning("4-bit quantization requires GPU. Falling back to CPU without quantization.")
                config["quantization"] = "none"
            
            # Load tokenizer from base model (not adapter) if adapter is used
            tokenizer_path = config["path"]
            try:
                # Try with fast tokenizer first
                tokenizer = AutoTokenizer.from_pretrained(
                    tokenizer_path,
                    cache_dir=self.cache_dir,
                    trust_remote_code=True,
                    use_fast=config.get("use_fast_tokenizer", True),
                    token=self.hf_token
                )
            except Exception as e:
                logger.warning(f"Fast tokenizer failed, trying legacy tokenizer: {e}")
                # Fallback to legacy tokenizer
                tokenizer = AutoTokenizer.from_pretrained(
                    tokenizer_path,
                    cache_dir=self.cache_dir,
                    trust_remote_code=True,
                    use_fast=False,
                    token=self.hf_token
                )

            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model (with or without adapter)
            if "adapter" in config and config["adapter"]:
                if PeftModel is None:
                    raise ImportError("peft library is required for adapter/LoRA support. Please install with 'pip install peft'.")
                # Load base model
                if self.device == "cpu":
                    base_model = AutoModelForCausalLM.from_pretrained(
                        config["path"],
                        cache_dir=self.cache_dir,
                        torch_dtype=torch.float32,
                        device_map=None,
                        trust_remote_code=True,
                        low_cpu_mem_usage=True,
                        token=self.hf_token
                    ).to("cpu")
                else:
                    base_model = AutoModelForCausalLM.from_pretrained(
                        config["path"],
                        quantization_config=quantization_config,
                        cache_dir=self.cache_dir,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        trust_remote_code=True,
                        token=self.hf_token
                    )
                # Load adapter on top
                model = PeftModel.from_pretrained(
                    base_model,
                    config["adapter"],
                    cache_dir=self.cache_dir,
                    token=self.hf_token
                )
            else:
                if self.device == "cpu":
                    model = AutoModelForCausalLM.from_pretrained(
                        config["path"],
                        cache_dir=self.cache_dir,
                        torch_dtype=torch.float32,
                        device_map=None,
                        trust_remote_code=True,
                        low_cpu_mem_usage=True,
                        token=self.hf_token
                    ).to("cpu")
                else:
                    model = AutoModelForCausalLM.from_pretrained(
                        config["path"],
                        quantization_config=quantization_config,
                        cache_dir=self.cache_dir,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        trust_remote_code=True,
                        token=self.hf_token
                    )
            # Create pipeline
            if self.device == "cpu":
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    device="cpu",
                    torch_dtype=torch.float32
                )
            else:
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    device=self.device,
                    torch_dtype=torch.float16
                )
            self.loaded_models[model_name] = {
                "pipeline": pipe,
                "tokenizer": tokenizer,
                "model": model,
                "config": config,
                "loaded_at": time.time()
            }
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
            
            # Clear model from memory
            model_data = self.loaded_models[model_name]
            del model_data["pipeline"]
            del model_data["model"]
            del model_data["tokenizer"]
            del self.loaded_models[model_name]
            
            # Force garbage collection
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
                # Try to load the model
                if not self.load_model(model_name):
                    raise Exception(f"Failed to load model '{model_name}'")
            
            model_data = self.loaded_models[model_name]
            pipeline = model_data["pipeline"]
            config = model_data["config"]
            
            # Use config defaults if not specified
            max_tokens = max_tokens or config.get("max_tokens", 512)
            temperature = temperature or config.get("temperature", 0.7)
            top_p = top_p or config.get("top_p", 0.9)
            
            start_time = time.time()
            
            # Generate response
            outputs = pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=pipeline.tokenizer.eos_token_id,
                return_full_text=False
            )
            
            processing_time = time.time() - start_time
            
            # Extract generated text
            generated_text = outputs[0]["generated_text"] if outputs else ""
            
            # Count tokens (approximate)
            tokens_used = len(pipeline.tokenizer.encode(prompt + generated_text))
            
            return {
                "response": generated_text.strip(),
                "model": model_name,
                "processing_time": processing_time,
                "tokens_used": tokens_used,
                "prompt_tokens": len(pipeline.tokenizer.encode(prompt)),
                "generated_tokens": tokens_used - len(pipeline.tokenizer.encode(prompt))
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response with model '{model_name}': {e}")
            # Provide more specific error messages
            if "numpy" in str(e).lower():
                raise Exception(f"NumPy compatibility issue: {e}. Please check NumPy installation.")
            elif "torch" in str(e).lower():
                raise Exception(f"PyTorch issue: {e}. Please check PyTorch installation.")
            else:
                raise Exception(f"Model inference failed: {e}")
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models."""
        return list(self.loaded_models.keys())
    
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is currently loaded."""
        return model_name in self.loaded_models
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model."""
        if model_name in self.model_configs:
            config = self.model_configs[model_name].copy()
            config["loaded"] = self.is_model_loaded(model_name)
            if model_name in self.loaded_models:
                config["loaded_at"] = self.loaded_models[model_name]["loaded_at"]
            return config
        return None


# Global model manager instance
model_manager = ModelManager() 