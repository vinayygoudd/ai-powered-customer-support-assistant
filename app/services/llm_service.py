import re
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class MockLLMProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        match = re.search(r"Customer message:\s*(.+?)(?:\nPredicted category:|\Z)", prompt, re.S)
        message = match.group(1).strip() if match else "your request"
        return (
            f'Thanks for contacting support. We received your request: "{message[:220]}". '
            "The ticket has been categorized and is being reviewed. "
            "Next step: a support team member will review the details and follow up with the appropriate resolution."
        )

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, model):
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.2)

    def generate(self, prompt: str) -> str:
        return self.llm.invoke(prompt).content

class LLMService:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    @classmethod
    def from_settings(cls, settings, prompt_manager=None):
        if settings.mock_llm or not settings.openai_api_key:
            return cls(MockLLMProvider())
        return cls(OpenAIProvider(settings.openai_api_key, settings.openai_model))

    def generate(self, prompt):
        return self.provider.generate(prompt)

    @staticmethod
    def validate_response(response):
        if not isinstance(response, str):
            return False
        text = re.sub(r"\s+", " ", response).strip()
        if not text or len(text) > 4000:
            return False
        forbidden_patterns = (
            r"OPENAI_API_KEY",
            r"sk-[A-Za-z0-9]{20,}",
            r"(?i)traceback \(most recent call last\)",
            r"(?i)api[_ -]?key\s*[:=]\s*\S+",
        )
        return not any(re.search(pattern, text) for pattern in forbidden_patterns)

    @staticmethod
    def safe_fallback():
        return (
            "Thanks for contacting support. We received your request. "
            "A support team member will review it and provide the next step."
        )
