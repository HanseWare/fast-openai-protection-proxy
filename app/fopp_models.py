from typing import List, Union, Literal
from pydantic import BaseModel, HttpUrl, Field


class TextInput(BaseModel):
    type: Literal["text"]
    text: str


class ImageUrl(BaseModel):
    url: str  # Erlaubt auch data:image/...-URLs (kein HttpUrl, um nicht zu blockieren)


class ImageInput(BaseModel):
    type: Literal["image_url"]
    image_url: ImageUrl


class StructuredModerationInput(BaseModel):
    __root__: Union[TextInput, ImageInput]


class ModerationRequest(BaseModel):
    model: str
    input: Union[
        str,                         # einfacher Text
        List[str],                   # Liste von Texten
        List[StructuredModerationInput]  # Liste strukturierter Inputs
    ]
    output_format: Literal["openai", "llama-guard-3"] = Field(default="openai")
