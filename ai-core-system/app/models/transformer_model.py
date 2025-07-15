from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from .base_model import BaseModel
from typing import Dict, Any

class TransformerModel(BaseModel):
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_info = {}

    def load_model(self, model_path: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device.type == 'cuda' else -1
        )
        self.model_info = {
            "path": model_path,
            "device": str(self.device),
            "type": "transformers"
        }

    def predict(self, input_text: str) -> Dict[str, Any]:
        if not self.pipeline:
            raise RuntimeError("Model not loaded.")
        outputs = self.pipeline(input_text, max_new_tokens=128)
        return {"generated_text": outputs[0]["generated_text"]}

    def get_model_info(self) -> Dict[str, Any]:
        return self.model_info 