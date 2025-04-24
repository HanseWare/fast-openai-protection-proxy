import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pythonjsonlogger.json import JsonFormatter

from api_v1 import api_v1_app
from utils import RESERVED_ATTRS

__name__ = "hanseware.fast-openai-protection-proxy"

logger = logging.getLogger(__name__)


class FOPP(FastAPI):
    base_url: str
    model_handler: Any
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")


def setup_logging():
    loglevel = os.getenv("FOPP_LOGLEVEL", "INFO").upper()
    logger.info("Setting log level from env to", loglevel)
    logging.basicConfig(level=logging.getLevelName(loglevel))
    logHandler = logging.StreamHandler()
    formatter = JsonFormatter(timestamp=True, reserved_attrs=RESERVED_ATTRS, datefmt='%Y-%m-%d %H:%M:%S')
    logHandler.setFormatter(formatter)
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(logHandler)
    uvi_logger = logging.getLogger("uvicorn.access")
    uvi_logger.handlers.clear()
    uvi_logger.addHandler(logHandler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


fopp_app = FOPP(lifespan=lifespan)

@fopp_app.get("/health")
async def health_check():
    return {"status": "ok"}

@fopp_app.get("/")
async def hello_world():
    return {"msg": "hello proxy"}

fopp_app.mount("/v1", app=api_v1_app)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("FOPP_HOST", "0.0.0.0")
    port = int(os.getenv("FOPP_PORT", 8000))
    uvicorn.run(fopp_app, host=host, port=port)