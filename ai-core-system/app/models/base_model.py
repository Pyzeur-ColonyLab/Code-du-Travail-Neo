from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseModel(ABC):
    @abstractmethod
    def load_model(self, model_path: str):
        pass

    @abstractmethod
    def predict(self, input_text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        pass 