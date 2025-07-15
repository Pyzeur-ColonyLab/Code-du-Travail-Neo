from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from app.models.base_model import BaseModel
from typing import Dict, Any, Optional

class TransformerModel(BaseModel):
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_info = {}

    def load_model(self, model_path: str, hf_token: Optional[str] = None, tokenizer_file: Optional[str] = None):
        tokenizer_kwargs = {}
        if tokenizer_file:
            tokenizer_kwargs['tokenizer_file'] = tokenizer_file
        if hf_token:
            tokenizer_kwargs['token'] = hf_token
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, **tokenizer_kwargs)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, token=hf_token)
        self.model.to(self.device)
        self.model.eval()
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1
        )
        self.model_info = {
            "model_path": model_path,
            "device": str(self.device),
            "tokenizer_file": tokenizer_file,
        }

    def predict(self, input_text: str) -> Dict[str, Any]:
        if not self.pipeline:
            raise RuntimeError("Model not loaded.")
        result = self.pipeline(input_text, max_new_tokens=128)
        return {"result": result}

    def get_model_info(self) -> Dict[str, Any]:
        return self.model_info 
