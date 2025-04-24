import logging
import os
import uuid
from typing import Any
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from fopp_models import CompletionRequest
from fopp_models import ModerationRequest
from guards_handler import handler as guards_handler
from guards_adapters import get_adapter, LlamaGuard3Adapter

__name__ = "hanseware.fast-openai-protection-proxy.api_v1"

logger = logging.getLogger(__name__)

class FOPP_API_V1(FastAPI):
    base_url: str
    guard_adapters: [Any] = {}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        for guard_name, guard_config in guards_handler.guards.items():
            self.guard_adapters[guard_name] = get_adapter(guard_config)


api_v1_app = FOPP_API_V1()

@api_v1_app.post("/moderations")
async def moderations(request: ModerationRequest):
    if isinstance(request.input, str):
        request.input = [request.input]

    if isinstance(request.input, list):
        results = []
        for input_text in request.input:
            if isinstance(input_text, str):
                adapter: LlamaGuard3Adapter = api_v1_app.guard_adapters[request.model]
                result = await adapter.run_openai_moderation(input_text)
                results.append(result)
            else:
                raise HTTPException(status_code=400, detail="Invalid input")
        response_object = {
            "id": str(uuid.uuid4()),
            "model": request.model,
            "results": results,
        }
        return JSONResponse(response_object, status_code=200)
    else:
        raise HTTPException(status_code=400, detail="Invalid input format")


@api_v1_app.post("/completions")
async def completions(request: CompletionRequest):
    if isinstance(request.prompt, str):
        request.prompt = [request.prompt]

    if isinstance(request.prompt, list):
        choices = []
        for input_text in request.prompt:
            if isinstance(input_text, str):
                adapter: LlamaGuard3Adapter = api_v1_app.guard_adapters[request.model]
                result = await adapter.run_custom_completion(input_text)
                choice = {
                    "text": result,
                    "index": len(choices),
                    "logprobs": None,
                    "finish_reason": "stop",
                }
                choices.append(choice)
            else:
                raise HTTPException(status_code=400, detail="Invalid input")

        response_object = {
            "id": str(uuid.uuid4()),
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": choices,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        return JSONResponse(response_object, status_code=200)
    else:
        raise HTTPException(status_code=400, detail="Invalid input format")