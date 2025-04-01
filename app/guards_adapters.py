from typing import Dict, Any

import httpx
from starlette.responses import JSONResponse

from fopp_models import GuardConfigModel

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


def get_adapter(guard_config: GuardConfigModel):
    if guard_config.guard_type == "llama-guard-3":
        return LlamaGuard3Adapter(guard_config)
    else:
        raise ValueError(f"Guard type {guard_config.guard_type} not supported")


class LlamaGuard3Adapter:
    guard_config: GuardConfigModel
    openai_safe_result: Dict[str, Any] = {}

    def __init__(self, guard_config):
        self.guard_config = guard_config
        self.openai_safe_result = {
            "flagged": False,
            "categories": OPENAI_DEFAULT_OUTPUTS,
            "category_scores": OPENAI_DEFAULT_OUTPUT_SCORES,
            "category_applied_input_types": OPENAI_DEFAULT_CATEGORY_APPLIED_INPUT_TYPES,
        }

    async def run_llama_guard_moderation(self, messages):
        return JSONResponse(status_code=501, content={"detail": "Not yet implemented"})

    async def run_openai_moderation(self, message):
        messages = [{"role": "user", "content": message}]
        prompt = self._prompt_header() + self._prompt_task("user") + self._prompt_categories() + self._prompt_conversation(messages) + self._promt_end("user")
        custom_timeout = httpx.Timeout(self.guard_config.request_timeout)

        headers = {
            "Content-Type": "application/json"
        }

        body = {"model": self.guard_config.target_model_name, "prompt": prompt}

        client = httpx.AsyncClient(timeout=custom_timeout)
        response = await client.post(self.guard_config.target, json=body, headers=headers)
        resp_body = response.json()
        if resp_body["choices"][0]["text"].strip().startswith("safe"):
            return self.openai_safe_result
        else:
            # TODO let the magic happen
            llama_guard_flagged_categories = resp_body["choices"][0]["text"].strip().split("\n")[1].split(",")
            # copy self.openai_safe_response as base for the flagged categories to local variable unsafe_response
            unsafe_result = self.openai_safe_result.copy()
            unsafe_result["flagged"] = True
            # set the flagged categories to True
            for category in llama_guard_flagged_categories:
                for openai_category in OPENAI_LLAMA_GUARD_CATEGORY_MAPPING[category]:
                    # set the category to True
                    unsafe_result["categories"][openai_category] = True
                    # set the score to 1.0
                    unsafe_result["category_scores"][openai_category] = 1.0
            return unsafe_result

    def _prompt_header(self):
        return f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>"

    def _prompt_task(self, role="user"):
        return f"Task: Check if there is unsafe content in '{role.capitalize()}' messages in conversations according to our safety policy with the below categories."

    def _prompt_categories(self):
        categories_string = [f"{category}\n" for category in self.guard_config.categories]
        return f"<BEGIN UNSAFE CONTENT CATEGORIES>\nCategories: {categories_string}<END UNSAFE CONTENT CATEGORIES>\n"

    def _prompt_conversation(self, messages):
        conversation = "<BEGIN CONVERSATION>\n"
        for message in messages:
            role = str(message["role"]).capitalize()
            content = str(message["content"])
            conversation += f"{role}: {content}\n"
        return conversation + "<END CONVERSATION>\n"

    def _promt_end(self, role="user"):
        return f"""Provide your safety assessment for ONLY THE LAST {role.capitalize()} message in the above conversation:
                    - First line must read 'safe' or 'unsafe'.
                    - If unsafe, a second line must include a comma-separated list of violated categories.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
