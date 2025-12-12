import os
from typing import List, Dict, Any, Union, Optional
from openai import OpenAI
from langchain_ollama import ChatOllama
from langchain_core.runnables import Runnable, RunnableConfig


class LLMWrapper(Runnable):

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3.1:8b",
        temperature: float = 0,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[Any]] = None,
    ):
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        self.api_key_str = api_key
        self.tags = tags or []
        self.metadata = metadata or {}
        self.callbacks = callbacks or []

        if self.provider == "openai":
            if not base_url:
                raise ValueError("base_url is required for openai provider")

            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
                or os.environ.get("HF_TOKEN")
                or os.environ.get("OPENAI_API_KEY"),
            )
            self._base_client = None
        elif self.provider == "ollama":
            try:
                self._base_client = ChatOllama(
                    model=model,
                    temperature=temperature,
                    tags=self.tags,
                    metadata=self.metadata,
                    callbacks=self.callbacks,
                )
                self.client = self._base_client
            except ImportError:
                raise ImportError(
                    "langchain_ollama is required for Ollama provider. "
                    "Install it with: pip install langchain-ollama"
                )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def with_config(
        self,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[Any]] = None,
    ):
        new_tags = self.tags + (tags or [])
        new_metadata = {**self.metadata, **(metadata or {})}
        new_callbacks = self.callbacks + (callbacks or [])

        new_instance = LLMWrapper(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature,
            base_url=self.base_url,
            api_key=self.api_key_str,
            tags=new_tags,
            metadata=new_metadata,
            callbacks=new_callbacks,
        )

        if self.provider == "ollama" and new_instance._base_client:
            new_instance.client = new_instance._base_client.with_config(
                tags=new_tags,
                metadata=new_metadata,
                callbacks=new_callbacks,
            )

        return new_instance

    def invoke(
        self,
        messages: Union[str, List[Dict[str, str]]],
        config: Optional[RunnableConfig] = None,
    ) -> "LLMResponse":
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        normalized_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                normalized_messages.append(msg)
            elif hasattr(msg, "type") and hasattr(msg, "content"):
                role = "system" if msg.type == "system" else msg.type
                normalized_messages.append({"role": role, "content": msg.content})
            else:
                normalized_messages.append({"role": "user", "content": str(msg)})

        if self.provider == "openai":
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=normalized_messages,
                temperature=self.temperature,
            )
            content = completion.choices[0].message.content

        elif self.provider == "ollama":
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

            lc_messages = []
            for msg in normalized_messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))

            response = self.client.invoke(lc_messages, config)
            content = response.content

        return LLMResponse(content)

    def stream(
        self,
        messages: Union[str, List[Dict[str, str]]],
        config: Optional[RunnableConfig] = None,
    ):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        normalized_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                normalized_messages.append(msg)
            elif hasattr(msg, "type") and hasattr(msg, "content"):
                role = "system" if msg.type == "system" else msg.type
                normalized_messages.append({"role": role, "content": msg.content})
            else:
                normalized_messages.append({"role": "user", "content": str(msg)})

        if self.provider == "openai":
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=normalized_messages,
                temperature=self.temperature,
                stream=True,
            )
            for chunk in stream:
                yield LLMResponse(chunk.choices[0].delta.content or "")

        elif self.provider == "ollama":
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

            lc_messages = []
            for msg in normalized_messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))

            for chunk in self.client.stream(lc_messages, config):
                yield chunk


class LLMResponse:

    def __init__(self, content: str):
        self.content = content

    def strip(self):
        return self.content.strip()

    def upper(self):
        return self.content.upper()
