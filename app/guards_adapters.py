from typing import Dict, Any

import httpx
from starlette.responses import JSONResponse

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

OPENAI_LLAMA_GUARD_CATEGORY_MAPPING = {
    "S1": ["violence", "violence/graphic"],
    "S2": ["harassment/threatening"],
    "S3": ["sexual", "harassment", "violence"],
    "S4": ["sexual/minors"],
    "S5": ["harassment"],
    "S6": [],
    "S7": [],
    "S8": [],
    "S9": ["violence"],
    "S10": ["hate", "hate/threatening"],
    "S11": ["self-harm", "self-harm/intent", "self-harm/instructions"],
    "S12": ["sexual"],
    "S13": []
}

OPENAI_DEFAULT_OUTPUTS = {
        "sexual": False,
        "hate": False,
        "harassment": False,
        "self-harm": False,
        "sexual/minors": False,
        "hate/threatening": False,
        "violence/graphic": False,
        "self-harm/intent": False,
        "self-harm/instructions": False,
        "harassment/threatening": False,
        "violence": False
}

OPENAI_DEFAULT_OUTPUT_SCORES = {
        "sexual": 0.0,
        "hate": 0.0,
        "harassment": 0.0,
        "self-harm": 0.0,
        "sexual/minors": 0.0,
        "hate/threatening": 0.0,
        "violence/graphic": 0.0,
        "self-harm/intent": 0.0,
        "self-harm/instructions": 0.0,
        "harassment/threatening": 0.0,
        "violence": 0.0
}

OPENAI_DEFAULT_CATEGORY_APPLIED_INPUT_TYPES = {
        "sexual": ["text"],
        "hate": ["text"],
        "harassment": ["text"],
        "self-harm": ["text"],
        "sexual/minors": ["text"],
        "hate/threatening": ["text"],
        "violence/graphic": ["text"],
        "self-harm/intent": ["text"],
        "self-harm/instructions": ["text"],
        "harassment/threatening": ["text"],
        "violence": ["text"]
}

class LlamaGuard3Adapter:
    guard_config: Dict[str, Any] = {}
    openai_safe_response: Dict[str, Any] = {}

    def __init__(self, guard_config):
        self.guard_config = guard_config
        self.openai_safe_response = {
            "id": "we-dont-care",
            "model": self.guard_config["target_model"],
            "results": [
                {
                    "flagged": False,
                    "categories": OPENAI_DEFAULT_OUTPUTS,
                    "category_scores": OPENAI_DEFAULT_OUTPUT_SCORES,
                    "category_applied_input_types": OPENAI_DEFAULT_CATEGORY_APPLIED_INPUT_TYPES,
                }
            ]
        }

    async def run_openai_moderation(self, message, categories=None):
        messages = [{"role": "user", "content": message}]
        prompt = self._prompt_header() + self._prompt_task("user") + self._prompt_categories(categories) + self._prompt_conversation(messages) + self._promt_end("user")
        custom_timeout = httpx.Timeout(self.guard_config["request_timeout"])

        headers = {
            "Content-Type": "application/json"
        }

        body = {"model": self.guard_config["target_model"], "prompt": prompt}

        client = httpx.AsyncClient(timeout=custom_timeout)
        response = await client.post(self.guard_config["target"], json=body, headers=headers)
        resp_body = response.json()
        if  resp_body["choices"][0]["text"].strip().startsWith("safe"):
            return JSONResponse(self.openai_safe_response)
        else:
            # TODO let the magic happen
            llama_guard_flagged_categories = resp_body["choices"][0]["text"].strip().split("\n")[1].split(",")
            # copy self.openai_safe_response as base for the flagged categories to local variable unsafe_response
            unsafe_response = self.openai_safe_response.copy()
            unsafe_response.results.flagged = True
            # set the flagged categories to True
            for category in llama_guard_flagged_categories:
                for openai_category in OPENAI_LLAMA_GUARD_CATEGORY_MAPPING[category]:
                    # set the category to True
                    unsafe_response["results"][0]["categories"][openai_category] = True
                    # set the score to 1.0
                    unsafe_response["results"][0]["category_scores"][openai_category] = 1.0
            return JSONResponse(self.openai_safe_response)

    def _prompt_header(self):
        return f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>"

    def _prompt_task(self, role = "user"):
        return f"Task: Check if there is unsafe content in '{role.capitalize()}' messages in conversations according to our safety policy with the below categories."

    def _prompt_categories(self, categories=None):
        if categories is None:
            categories = DEFAULT_CONTENT_CATEGORIES_LLAMA_GUARD
        categories_string = [f"{category}\n" for category in categories]
        return f"<BEGIN UNSAFE CONTENT CATEGORIES>\nCategories: {categories_string}<END UNSAFE CONTENT CATEGORIES>\n"

    def _prompt_conversation(self, messages):
        conversation = "<BEGIN CONVERSATION>\n"
        for message in messages:
            conversation += f"{str(message.role).capitalize()}: {message.content}\n"
        return conversation + "<END CONVERSATION>\n"


    def _promt_end(self, role = "user"):
        return f"""Provide your safety assessment for ONLY THE LAST {role.capitalize()} message in the above conversation:
                    - First line must read 'safe' or 'unsafe'.
                    - If unsafe, a second line must include a comma-separated list of violated categories.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
