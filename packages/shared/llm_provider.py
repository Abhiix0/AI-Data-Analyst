"""LLM provider abstraction supporting Groq, OpenAI, Anthropic, and deterministic Mock."""
from __future__ import annotations
import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    raw: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        """Generate response from messages."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        """Generate a response parsed strictly into a Pydantic schema."""
        pass


class GroqLLMProvider(BaseLLMProvider):
    """Groq API provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.model = os.environ.get("GROQ_MODEL", model)
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable or argument is required.")
        from groq import Groq
        self.client = Groq(api_key=self.api_key)

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        payload_messages = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        chat_completion = self.client.chat.completions.create(**kwargs)
        choice = chat_completion.choices[0]
        content = choice.message.content or ""
        return LLMResponse(content=content)

    def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_instruction = (
            f"\nYou must respond ONLY with a valid JSON object strictly matching this schema:\n{schema_json}\n"
            "Do not output markdown codeblocks, explanations, or text outside the JSON object."
        )
        augmented_messages = [
            LLMMessage(role="system", content=messages[0].content + system_instruction)
            if messages and messages[0].role == "system"
            else LLMMessage(role="system", content=system_instruction)
        ] + [m for m in messages if m.role != "system" or m != messages[0]]

        resp = self.generate(augmented_messages, temperature=temperature, response_format="json")
        cleaned_content = re.sub(r"^```json\s*", "", resp.content.strip())
        cleaned_content = re.sub(r"\s*```$", "", cleaned_content).strip()
        return schema.model_validate_json(cleaned_content)


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_MODEL", model)
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable or argument is required.")
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        payload_messages = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        resp = self.client.chat.completions.create(**kwargs)
        return LLMResponse(content=resp.choices[0].message.content or "")

    def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        payload_messages = [{"role": m.role, "content": m.content} for m in messages]
        resp = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=payload_messages,
            response_format=schema,
            temperature=temperature,
        )
        return resp.choices[0].message.parsed


class AnthropicLLMProvider(BaseLLMProvider):
    """Anthropic API provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = os.environ.get("ANTHROPIC_MODEL", model)
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or argument is required.")
        from anthropic import Anthropic
        self.client = Anthropic(api_key=self.api_key)

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m.role == "system":
                system_msg += m.content + "\n"
            else:
                user_msgs.append({"role": m.role, "content": m.content})

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": user_msgs,
            "temperature": temperature,
        }
        if system_msg.strip():
            kwargs["system"] = system_msg.strip()

        resp = self.client.messages.create(**kwargs)
        content_text = "".join([block.text for block in resp.content if hasattr(block, "text")])
        return LLMResponse(content=content_text)

    def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_instruction = (
            f"\nYou must respond ONLY with a valid JSON object strictly matching this schema:\n{schema_json}\n"
            "Do not output markdown codeblocks, explanations, or text outside the JSON object."
        )
        augmented = [LLMMessage(role="system", content=system_instruction)] + messages
        resp = self.generate(augmented, temperature=temperature)
        cleaned = re.sub(r"^```json\s*", "", resp.content.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        return schema.model_validate_json(cleaned)


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for offline testing and deterministic agent execution."""

    def __init__(self, canned_responses: Optional[Dict[str, Any]] = None):
        self.canned_responses = canned_responses or {}

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        last_msg = messages[-1].content if messages else ""
        for key, resp in self.canned_responses.items():
            if key in last_msg:
                if isinstance(resp, str):
                    return LLMResponse(content=resp)
                elif isinstance(resp, BaseModel):
                    return LLMResponse(content=resp.model_dump_json())
                elif isinstance(resp, dict):
                    return LLMResponse(content=json.dumps(resp))
        return LLMResponse(content='{"status": "ok", "message": "mocked response"}')

    def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        last_msg = messages[-1].content if messages else ""
        for key, resp in self.canned_responses.items():
            if key in last_msg:
                if isinstance(resp, schema):
                    return resp
                if isinstance(resp, dict):
                    return schema.model_validate(resp)
                if isinstance(resp, str):
                    return schema.model_validate_json(resp)
        # Attempt to create default empty schema
        try:
            return schema()  # type: ignore
        except Exception:
            # Generate mock from fields
            fields_data: Dict[str, Any] = {}
            for fname, field in schema.model_fields.items():
                annotation = field.annotation
                if annotation == str:
                    fields_data[fname] = "mock_value"
                elif annotation == int:
                    fields_data[fname] = 1
                elif annotation == float:
                    fields_data[fname] = 1.0
                elif annotation == bool:
                    fields_data[fname] = True
                elif getattr(annotation, "__origin__", None) is list:
                    fields_data[fname] = []
                elif getattr(annotation, "__origin__", None) is dict:
                    fields_data[fname] = {}
                else:
                    fields_data[fname] = None
            return schema.model_validate(fields_data)


def get_llm_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMProvider:
    """Factory creating configured LLM provider."""
    provider = (provider_name or os.environ.get("LLM_PROVIDER", "")).lower()

    if provider == "groq" or (not provider and os.environ.get("GROQ_API_KEY")):
        return GroqLLMProvider(api_key=api_key, model=model or "llama-3.3-70b-versatile")
    elif provider == "openai" or (not provider and os.environ.get("OPENAI_API_KEY")):
        return OpenAILLMProvider(api_key=api_key, model=model or "gpt-4o")
    elif provider == "anthropic" or (not provider and os.environ.get("ANTHROPIC_API_KEY")):
        return AnthropicLLMProvider(api_key=api_key, model=model or "claude-3-5-sonnet-20241022")
    else:
        # Fallback to Mock if no keys provided
        return MockLLMProvider()
