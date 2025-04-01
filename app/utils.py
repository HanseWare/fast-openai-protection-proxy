from typing import List

RESERVED_ATTRS: List[str] = [
    "args",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
]

DEFAULT_CONTENT_CATEGORIES_LLAMA_GUARD = [
    "S1: Violent Crimes.",
    "S2: Non-Violent Crimes.",
    "S3: Sex Crimes.",
    "S4: Child Exploitation.",
    "S5: Defamation.",
    "S6: Specialized Advice.",
    "S7: Privacy.",
    "S8: Intellectual Property.",
    "S9: Indiscriminate Weapons.",
    "S10: Hate.",
    "S11: Self-Harm.",
    "S12: Sexual Content.",
    "S13: Elections."
]