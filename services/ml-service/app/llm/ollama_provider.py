import httpx

from app.config import settings
from app.llm.provider import LlmProvider


class OllamaProvider(LlmProvider):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self._model = settings.llm_model

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        resp = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self._model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {"num_predict": max_tokens, "temperature": 0.2},
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()
