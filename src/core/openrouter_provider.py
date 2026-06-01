import time
from typing import Dict, Any, Optional, Generator
from openai import OpenAI
from src.core.llm_provider import LLMProvider


class OpenRouterProvider(LLMProvider):
    """
    LLM Provider cho OpenRouter.ai
    Dùng OpenAI-compatible API với base_url khác.
    Xem danh sách model: https://openrouter.ai/models
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        model_name: str = "meta-llama/llama-3.1-8b-instruct:free",
        api_key: Optional[str] = None,
        site_url: str = "http://localhost:5000",
        site_name: str = "VinUni Room Finder",
    ):
        super().__init__(model_name, api_key)
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
        )
        # OpenRouter khuyến nghị thêm headers này
        self.extra_headers = {
            "HTTP-Referer": site_url,
            "X-Title": site_name,
        }

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            extra_headers=self.extra_headers,
        )

        latency_ms = int((time.time() - start_time) * 1000)
        content = response.choices[0].message.content or ""
        usage = {
            "prompt_tokens":     getattr(response.usage, "prompt_tokens", 0),
            "completion_tokens": getattr(response.usage, "completion_tokens", 0),
            "total_tokens":      getattr(response.usage, "total_tokens", 0),
        }

        return {
            "content":    content,
            "usage":      usage,
            "latency_ms": latency_ms,
            "provider":   "openrouter",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            extra_headers=self.extra_headers,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
