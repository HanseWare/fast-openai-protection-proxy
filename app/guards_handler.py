import json
import os
from typing import Dict, Any

from fastapi import HTTPException


class GuardsHandler:
    guards: Dict[str, Any] = {}

    def __init__(self):
        self.guards = {}
        config_dir = os.getenv("FOPP_CONFIG_DIR", "/configs")
        for filename in os.listdir(config_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(config_dir, filename)
                with open(filepath, "r") as f:
                    config = json.load(f)
                    # Process the config
                    self.load_config(config)

    def load_config(self, config: Dict[str, Any]):
        for provider_name, provider_config in config.items():
            prefix = provider_config.get("prefix", "")
            models = provider_config.get("models", {})
            # Use api_key_variable to read the api_key from environment variable, default api_key to "ignored" if no api_key_variable is provided
            api_key = "ignored"
            if provider_config.get("api_key_variable"):
                api_key = os.getenv(provider_config.get("api_key_variable"), "ignored")
            for model_name in models.keys():
                self.guards[f"{prefix}{model_name}"] = {
                    "api_key": api_key,
                    "data": models[model_name]
                }

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
