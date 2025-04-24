from typing import List, Union, Literal, Optional, Dict

from pydantic import BaseModel, Field, RootModel


class TextInput(BaseModel):
    type: Literal["text"]
    text: str


class ImageUrl(BaseModel):
    url: str  # Erlaubt auch data:image/...-URLs (kein HttpUrl, um nicht zu blockieren)


class ImageInput(BaseModel):
    type: Literal["image_url"]
    image_url: ImageUrl


class StructuredModerationInput(RootModel[Union[TextInput, ImageInput]]):
    pass


class ModerationRequest(BaseModel):
    model: Optional[str] = "llama-guard-3-1b"
    input: Union[
        str,                         # einfacher Text
        List[str],                   # Liste von Texten
        List[StructuredModerationInput]  # Liste strukturierter Inputs
    ]
    output_format: Literal["openai", "llama-guard-3"] = Field(default="openai")

class CompletionRequest(BaseModel):
    model: Optional[str] = "llama-guard-3-1b"
    prompt: Union[
        str,                         # einfacher Text
        List[str],                   # Liste von Texten
    ]

class GuardConfigModel(BaseModel):
    guard_type: str
    api_key: Optional[str] = 'ignored'
    categories: Optional[List[str]] = None
    input_types: Optional[List[str]] = ["text"]
    target: str
    target_model_name: str
    request_timeout: Optional[int] = 10

class GuardConfig(BaseModel):
    api_key_variable: Optional[str] = 'ignored'
    prefix: Optional[str] = ""
    models: Dict[str, GuardConfigModel] = {}
