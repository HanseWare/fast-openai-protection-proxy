import os
from typing import Optional, List
import logging

import httpx
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse, Response

from app.fopp_models import ModerationRequest
from auth import can_request

__name__ = "hanseware.fast-openai-protection-proxy.api_v1"

logger = logging.getLogger(__name__)

class FOPP_API_V1(FastAPI):
    base_url: str
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")

app = FOPP_API_V1()

@app.post("/moderations")
async def chat_completions(request: ModerationRequest):
    return JSONResponse(status_code=501, content={"detail": "Not yet implemented"})
