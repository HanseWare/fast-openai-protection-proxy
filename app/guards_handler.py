import json
import os
from typing import Dict, Any

from fastapi import HTTPException

from fopp_models import GuardConfig, GuardConfigModel
from utils import DEFAULT_CONTENT_CATEGORIES_LLAMA_GUARD


class GuardsHandler:
    guards: Dict[str, GuardConfigModel] = {}

    def __init__(self):
        self.guards = {}
        config_dir = os.getenv("FOPP_CONFIG_DIR", "/configs")
        for filename in os.listdir(config_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(config_dir, filename)
                with open(filepath, "r") as f:
                    config_data = json.load(f)
                    # Process the config
                    self.load_config(config_data)

    def load_config(self, config: Dict[str, Any]):
        for provider_name, provider_config in config.items():
            new_config = GuardConfig(**provider_config)
            prefix = new_config.prefix
            models = new_config.models
            # Use api_key_variable to read the api_key from environment variable, default api_key to "ignored" if no api_key_variable is provided
            api_key = None
            if new_config.api_key_variable:
                api_key = os.getenv(new_config.api_key_variable, "ignored")
            for model_name, model in models.items():
                # check if model entry has custom_categories
                # if not, set it to Default from utils
                if model.categories is None and "llama-guard-3" == model.guard_type:
                    model.categories = DEFAULT_CONTENT_CATEGORIES_LLAMA_GUARD
                if api_key:
                    model.api_key = api_key

                self.guards[f"{prefix}{model_name}"] = model

    def get_guard_data(self, guard, input_types=None):
        guard_entry = self.guards.get(guard, None)
        supported_types = guard_entry.get("input_types", None)
        if not guard_entry:
            raise HTTPException(status_code=404, detail=f"Guard {guard} not found")
        if not input_types:
            return guard_entry
        if all(input_type in supported_types for input_type in input_types):
            return guard_entry
        raise HTTPException(status_code=400, detail=f"Input type(s) not supported for guard model {guard}")

handler = GuardsHandler()
