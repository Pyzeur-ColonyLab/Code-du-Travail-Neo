from .transformer_model import TransformerModel

class ModelFactory:
    _models = {
        "transformer": TransformerModel,
        # Add other models here
    }

    @classmethod
    def create_model(cls, model_name: str):
        if model_name not in cls._models:
            raise ValueError(f"Unknown model: {model_name}")
        return cls._models[model_name]()

    @classmethod
    def register_model(cls, name: str, model_cls):
        cls._models[name] = model_cls

    @classmethod
    def list_models(cls):
        return list(cls._models.keys()) 