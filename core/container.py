import asyncio
from dataclasses import dataclass, field
from functools import cached_property
from typing import Callable, Literal, TypeVar

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatResult
from langchain_core.language_models.base import LanguageModelInput
from openai.types.chat import ChatCompletion
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel


from core.config import settings
from core.entities import CostTracker
from core.prompt_config import PromptConfig, default_prompt_config
from core.schemas import StreamEvent, StreamKind
from core.mcp_clients.filesystem.mcp_client_base import FilesystemMcpClient
from core.mcp_clients.filesystem.local_filesystem_client import LocalFileSystemClient
from core.web_search.base import SearchManager
from core.web_search.exa import ExaSearch
from core.web_search.noop import NoopSearch
from core.db import OverviewCache
from lib.logger import get_logger
from lib.helpers import log_duration

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class ReasoningStreamMixin:
    """Captures non-standard reasoning fields from OpenAI-compatible
    streaming chunks that ChatOpenAI ignores by design."""

    def _convert_chunk_to_generation_chunk(
        self, chunk, default_chunk_class, base_generation_info
    ):
        gen_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        if gen_chunk is None:
            return gen_chunk
        try:
            choices = chunk.get("choices", []) or chunk.get("chunk", {}).get(
                "choices", []
            )
            if not choices:
                return gen_chunk
            delta = choices[0].get("delta") or {}
            reasoning = delta.get("reasoning") or delta.get("reasoning_content")
            if reasoning:
                gen_chunk.message.additional_kwargs["reasoning_content"] = reasoning
        except Exception as e:
            logger.warning(f"Reasoning stream extraction failed: {e}")
        return gen_chunk


class ReasoningChatOpenAI(ReasoningStreamMixin, ChatOpenAI):
    """ChatOpenAI that preserves reasoning fields during streaming."""

    pass


class KimiChatOpenAI(ReasoningStreamMixin, ChatOpenAI):
    """ChatOpenAI subclass that preserves reasoning_content on assistant
    messages — required by Moonshot when thinking is enabled and tool calls
    appear in the history.

    langchain-openai doesn't know about Moonshot's reasoning_content field,
    so we extract it from the raw response in _create_chat_result and replay
    it in _get_request_payload.
    """

    kimi_reasoning: bool = False

    def _create_chat_result(
        self, response: ChatCompletion | dict, generation_info: dict | None = None
    ) -> ChatResult:
        result = super()._create_chat_result(response, generation_info)
        try:
            if hasattr(response, "choices"):
                choices = response.choices
            elif isinstance(response, dict):
                choices = response.get("choices", [])
            else:
                choices = []

            for gen, choice in zip(result.generations, choices):
                rc = None
                if hasattr(choice, "message"):
                    msg = choice.message
                    rc = getattr(msg, "reasoning_content", None)
                    if rc is None and hasattr(msg, "model_extra"):
                        rc = (msg.model_extra or {}).get("reasoning_content")
                elif isinstance(choice, dict):
                    msg = choice.get("message", {})
                    if isinstance(msg, dict):
                        rc = msg.get("reasoning_content")
                if rc:
                    gen.message.additional_kwargs["reasoning_content"] = rc
        except Exception as e:
            logger.warning(f"KimiChatOpenAI: failed to extract reasoning_content: {e}")
        return result

    def _get_request_payload(
        self, input_: LanguageModelInput, *, stop: list[str] | None = None, **kwargs
    ) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)

        thinking = {"type": "enabled" if self.kimi_reasoning else "disabled"}
        if self.kimi_reasoning:
            thinking["keep"] = "all"

        extra_body = payload.get("extra_body") or {}
        extra_body["thinking"] = thinking
        payload["extra_body"] = extra_body

        try:
            messages_in = input_ if isinstance(input_, list) else input_.to_messages()
        except Exception:
            return payload

        serialized = payload.get("messages", [])
        ai_idx = 0
        for msg in messages_in:
            if not isinstance(msg, AIMessage):
                continue
            rc = msg.additional_kwargs.get("reasoning_content")
            while (
                ai_idx < len(serialized)
                and serialized[ai_idx].get("role") != "assistant"
            ):
                ai_idx += 1
            if ai_idx >= len(serialized):
                break
            if rc:
                serialized[ai_idx]["reasoning_content"] = rc
            ai_idx += 1

        return payload


@dataclass
class Llm:
    provider: str
    invoker: BaseChatModel
    cost_tracker: CostTracker
    stream_listener: Callable[[StreamEvent], None] | None
    do_cancel: Callable[[], bool]
    reasoning: bool

    def bind_tools(self, tools, **kwargs) -> "Llm":
        return Llm(
            provider=self.provider,
            invoker=self.invoker.bind_tools(tools, **kwargs),
            cost_tracker=self.cost_tracker,
            stream_listener=self.stream_listener,
            do_cancel=self.do_cancel,
            reasoning=self.reasoning,
        )

    async def ainvoke(self, messages: LanguageModelInput, **kwargs) -> AIMessage:
        async with log_duration() as log_body:
            extra_body = self._extra_body()
            stream_kwargs = (
                {"extra_body": extra_body, **kwargs} if extra_body else kwargs
            )

            aggregate: AIMessageChunk | None = None
            async for chunk in self.invoker.astream(messages, **stream_kwargs):
                if self.do_cancel():
                    self._post_to_stream(kind=StreamKind.END)
                    log_body.update({"canceled": True})
                    raise asyncio.CancelledError("Manually cancelled")
                if aggregate is None:
                    self._post_to_stream(StreamKind.START)
                    aggregate = chunk
                else:
                    aggregate += chunk
                for kind, delta in self._extract_deltas(chunk):
                    self._post_to_stream(kind, delta)
            self._post_to_stream(kind=StreamKind.END)

            response = aggregate if aggregate is not None else AIMessage(content="")
            log_body.update(response.response_metadata)

        cost = 0.0
        try:
            cost = response.response_metadata.get("token_usage", {}).get("cost", 0)
        except Exception:
            logger.info(f"Failed to get cost, metadata: \n{response.response_metadata}")
        self.cost_tracker.add_cost(float(cost or 0))

        return response

    async def ainvoke_structured(
        self, schema: type[T], messages: LanguageModelInput, **kwargs
    ) -> T:
        self._post_to_stream(StreamKind.START, can_stop=False)
        async with log_duration() as log_body:
            structured = self.invoker.with_structured_output(
                schema, include_raw=True, **self._struct_kwargs(kwargs)
            )
            extra_body = self._extra_body()
            if extra_body:
                response = await structured.ainvoke(messages, extra_body=extra_body)
            else:
                response = await structured.ainvoke(messages)
            raw: AIMessage = response["raw"]
            log_body.update(raw.response_metadata)
        self._post_to_stream(StreamKind.END)

        cost = 0.0
        try:
            cost = raw.response_metadata.get("token_usage", {}).get("cost", 0)
        except Exception:
            logger.info(f"Failed to get cost, metadata: \n{raw.response_metadata}")
        self.cost_tracker.add_cost(float(cost or 0))

        return response["parsed"]

    def _struct_kwargs(self, kwargs: dict) -> dict:
        struct_kwargs = dict(kwargs)
        if self.provider == "nvidia":
            model_name = getattr(self.invoker, "model", "").lower()
            if "nemotron" in model_name:
                struct_kwargs.setdefault("method", "json_mode")
        return struct_kwargs

    def _post_to_stream(self, kind: StreamKind, data: str = "", can_stop: bool = True):
        if self.stream_listener:
            self.stream_listener(StreamEvent(kind=kind, delta=data, can_stop=can_stop))

    def _extra_body(self) -> dict:
        body = {}

        if self.provider == "openrouter":
            body["include_cost"] = True
            if self.reasoning:
                body["reasoning"] = {"effort": "high"}

        if self.provider == "google":
            pass

        if self.provider == "alibaba":
            body["enable_thinking"] = self.reasoning

        if self.provider == "nvidia":
            model = getattr(self.invoker, "model", "") or ""
            if "nemotron" in model.lower():
                pass
            elif "kimi" in model.lower():
                body["chat_template_kwargs"] = {"thinking": self.reasoning}
            else:
                body["reasoning_effort"] = "high" if self.reasoning else "none"
                body["chat_template_kwargs"] = {
                    "enable_thinking": self.reasoning,
                    "thinking": self.reasoning,
                }

        if self.provider == "kimi":
            pass

        if self.provider == "mimo":
            pass

        if self.is_openai():
            body["provider"] = {"order": ["OpenAI"]}
            body["prompt_caching"] = True

        if self.is_deepseek():
            body["prompt_caching"] = True

        return body

    def is_openai(self) -> bool:
        model = getattr(self.invoker, "model", "") or ""
        return "openai" in model

    def is_deepseek(self) -> bool:
        model = getattr(self.invoker, "model", "") or ""
        return "deepseek" in model

    @staticmethod
    def _extract_deltas(chunk) -> list[tuple[StreamKind, str]]:
        """Returns list of (kind, text) tuples from a chunk."""
        out = []

        # Text content — string or content-block list.
        content = chunk.content
        if isinstance(content, str):
            if content:
                out.append((StreamKind.TEXT, content))
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text":
                    text = block.get("text", "")
                    if text:
                        out.append((StreamKind.TEXT, text))
                elif btype == "thinking":
                    text = block.get("thinking", "") or block.get("text", "")
                    if text:
                        out.append((StreamKind.REASONING, text))

        # Provider-specific reasoning in additional_kwargs.
        kwargs = getattr(chunk, "additional_kwargs", {}) or {}
        reasoning = kwargs.get("reasoning_content") or kwargs.get("reasoning")
        if reasoning:
            # Some providers send dicts with summary/details — flatten to text.
            if isinstance(reasoning, str):
                out.append((StreamKind.REASONING, reasoning))
            elif isinstance(reasoning, dict):
                text = reasoning.get("content") or reasoning.get("summary") or ""
                if text:
                    out.append((StreamKind.REASONING, text))

        return out


@dataclass
class AgentContainer:
    mcp_client: FilesystemMcpClient = field(default=None)
    web_search: SearchManager = field(default=None)
    prompt_config: PromptConfig = field(default=None)
    overview_cache: OverviewCache = field(default=None)
    cost_tracker: CostTracker = field(default_factory=CostTracker)
    stream_listener: Callable[[StreamEvent], None] | None = None
    model_mode: Literal["standard", "high"] = "high"
    cancel: bool = False

    def __post_init__(self) -> None:
        if self.mcp_client is None:
            self.mcp_client = LocalFileSystemClient()
        if self.web_search is None:
            self.set_web_search()
        if self.prompt_config is None:
            self.prompt_config = default_prompt_config
        if self.overview_cache is None:
            self.overview_cache = OverviewCache()

    def set_web_search(self) -> None:
        if settings.exa_api_key:
            self.web_search = ExaSearch(settings.exa_api_key)
        else:
            self.web_search = NoopSearch()

    def set_model_mode(self, mode: Literal["standard", "high"]) -> None:
        self.model_mode = mode
        self.invalidate_llm_cache()
        logger.info(f"LLM model mode set to {mode}")

    def set_stream_listener(self, stream_listener: Callable[[StreamEvent], None]):
        self.stream_listener = stream_listener
        self.invalidate_llm_cache()

    def invalidate_llm_cache(self):
        for attr in (
            "llm_strict",
            "llm_coding",
            "llm_balanced",
            "llm_creative",
        ):
            self.__dict__.pop(attr, None)

    def create_llm(
        self, provider: str, model: str, temperature: float, reasoning: bool, **kwargs
    ) -> Llm:

        if provider == "openrouter":
            invoker = ReasoningChatOpenAI(
                model=model,
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                default_headers={
                    "HTTP-Referer": settings.openrouter_http_referer,
                    "X-Title": settings.openrouter_app_title,
                },
                temperature=temperature,
                **kwargs,
            )
        elif provider == "alibaba":
            invoker = ReasoningChatOpenAI(
                model=model,
                api_key=settings.alibaba_api_key,
                base_url=settings.alibaba_base_url,
                default_headers={},
                temperature=temperature,
                **kwargs,
            )
        elif provider == "google":
            google_kwargs = dict(kwargs)
            if "gemma" not in model:
                if "gemini-3" in model or "gemini-4" in model:
                    google_kwargs.setdefault(
                        "thinking_level", "high" if reasoning else "low"
                    )
                else:
                    google_kwargs.setdefault("thinking_budget", -1 if reasoning else 0)
                if reasoning:
                    google_kwargs.setdefault("include_thoughts", True)

            invoker = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=settings.google_api_key,
                temperature=temperature,
                **google_kwargs,
            )
        elif provider == "nvidia":
            invoker = ReasoningChatOpenAI(
                model=model,
                api_key=settings.nvidia_api_key,
                base_url=settings.nvidia_base_url,
                default_headers={},
                temperature=temperature,
                **kwargs,
            )
        elif provider == "kimi":
            invoker = KimiChatOpenAI(
                model=model,
                api_key=settings.kimi_api_key,
                base_url=settings.kimi_base_url,
                default_headers={"User-Agent": "KimiCLI/1.3"},
                temperature=temperature,
                kimi_reasoning=reasoning,
                **kwargs,
            )
        elif provider == "mimo":
            invoker = ReasoningChatOpenAI(
                model=model,
                api_key=settings.mimo_api_key,
                base_url=settings.mimo_base_url,
                default_headers={},
                temperature=temperature,
                **kwargs,
            )
        else:
            raise NotImplementedError(f"{provider} is not supported")

        return Llm(
            provider,
            invoker,
            self.cost_tracker,
            self.stream_listener,
            self.do_cancel,
            reasoning,
        )

    async def get_ignore_list(self) -> list[str]:
        content = await self.mcp_client.get_file_text(".nice/.ignore")
        return content.split("\n")

    def do_cancel(self) -> bool:
        return_val = self.cancel
        self.cancel = False
        return return_val

    @property
    def summarization_model(self) -> tuple[str, str]:
        return (
            settings.summarization_model_provider,
            settings.summarization_model,
        )

    @property
    def strict_model(self) -> tuple[str, str]:
        if self.model_mode == "high":
            return (
                settings.strict_model_high_provider,
                settings.strict_model_high,
            )
        return settings.strict_model_provider, settings.strict_model

    @property
    def creative_model(self) -> tuple[str, str]:
        if self.model_mode == "high":
            return (
                settings.creative_model_high_provider,
                settings.creative_model_high,
            )
        return (
            settings.creative_model_provider,
            settings.creative_model,
        )

    @cached_property
    def llm_summarization(self) -> Llm:
        provider, model = self.summarization_model
        return self.create_llm(provider, model, 0.2, False)

    @cached_property
    def llm_strict(self) -> Llm:
        provider, model = self.strict_model
        return self.create_llm(provider, model, 0.1, False)

    @cached_property
    def llm_coding(self) -> Llm:
        provider, model = self.creative_model
        return self.create_llm(provider, model, 0.1, False)

    @cached_property
    def llm_balanced(self) -> Llm:
        provider, model = self.creative_model
        return self.create_llm(provider, model, 0.2, True)

    @cached_property
    def llm_creative(self) -> Llm:
        provider, model = self.creative_model
        return self.create_llm(provider, model, 0.4, True)


_default_container: AgentContainer | None = None


def get_container() -> AgentContainer:
    global _default_container
    if _default_container is None:
        _default_container = AgentContainer()
    assert _default_container
    return _default_container


def override_container(container: AgentContainer) -> None:
    global _default_container
    _default_container = container


def reset_container() -> None:
    global _default_container
    _default_container = None
