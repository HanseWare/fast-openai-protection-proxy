import logging
import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from fopp_models import ModerationRequest
from guards_handler import handler as guards
from guards_adapters import get_adapter, LlamaGuard3Adapter

__name__ = "hanseware.fast-openai-protection-proxy.api_v1"

logger = logging.getLogger(__name__)

class FOPP_API_V1(FastAPI):
    base_url: str
    guard_adapters: [Any] = {}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        for guard_name, guard_config in guards:
            self.guard_adapters[guard_name] = get_adapter(guard_config)


fopp_app = FOPP_API_V1()

@fopp_app.post("/moderations")
async def chat_completions(request: ModerationRequest):
    if request.output_format == "openai":
        if isinstance(request.input, str):
            request.input = [request.input]

        if isinstance(request.input, list):
            results = []
            for input_text in request.input:
                if isinstance(input_text, str):
                    adapter: LlamaGuard3Adapter = fopp_app.guard_adapters[request.model]
                    result = await adapter.run_openai_moderation(input_text)
                    results.append(result)
                else:
                    raise HTTPException(status_code=400, detail="Invalid input")
            response_object = {
                "id": uuid.uuid4(),
                "model": request.model,
                "results": results,
            }
            return JSONResponse(response_object, status_code=200)
        else:
            raise HTTPException(status_code=400, detail="Invalid input format")
    return JSONResponse(status_code=501, content={"detail": "Not yet implemented"})
