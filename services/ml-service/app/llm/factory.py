from app.config import settings
from app.llm.provider import LlmProvider


def get_llm_provider() -> LlmProvider:
    provider = settings.llm_provider
    if provider == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider()
    if provider == "bedrock":
        from app.llm.bedrock_provider import BedrockProvider
        return BedrockProvider()
    if provider == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    raise ValueError(f"unknown LLM_PROVIDER: {provider}")
