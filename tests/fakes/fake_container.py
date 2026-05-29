from dataclasses import dataclass, field
import json


@dataclass
class FakeTool:
    name: str
    result: object
    calls: list = field(default_factory=list)

    async def ainvoke(self, args):
        self.calls.append(args)
        return self.result


@dataclass
class FakeMCPClient:
    overview_text: str
    calls: list = field(default_factory=list)
    tree_text: str = "fake file tree\n"
    file_content_overrides: dict = field(default_factory=dict)

    async def get_file_text(self, path):
        self.calls.append(path)
        return self.file_content_overrides.get(path, self.overview_text)

    async def list_directory_tree(self) -> str:
        return json.dumps({"tree": self.tree_text})


@dataclass
class FakePromptConfig:
    tools: list
    build_context_prompt: str = "build context prompt"
    user_prefix: str = "[Coding Agent — user request]"
    planning_system_prompt: str = "planning system prompt"
    planning_review_prompt: str = "planning review prompt"

    def __post_init__(self):
        self.build_context_tools = self.tools


@dataclass
class FakeAppSettings:
    agent_max_steps: int = 20


@dataclass
class FakeBoundLLM:
    responses: list
    invocations: list = field(default_factory=list)

    async def ainvoke(self, messages):
        self.invocations.append(list(messages))
        return self.responses.pop(0)


@dataclass
class FakeLLM:
    responses: list
    bound_tools: list | None = None
    bound_llm: FakeBoundLLM = field(init=False)

    def __post_init__(self):
        self.bound_llm = FakeBoundLLM(self.responses)

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self.bound_llm

    async def ainvoke(self, messages):
        return await self.bound_llm.ainvoke(messages)

    async def ainvoke_structured(self, schema, messages):
        response = await self.bound_llm.ainvoke(messages)
        return schema.model_validate_json(response.content)


@dataclass
class FakeLLMStrict(FakeLLM):
    pass


@dataclass
class FakeLLMCoding(FakeLLM):
    pass


@dataclass
class FakeLLMBalanced(FakeLLM):
    pass


@dataclass
class FakeLLMCreative(FakeLLM):
    pass


@dataclass
class FakeContainer:
    overview_text: str
    llm_responses_strict: list = field(default_factory=list)
    llm_responses_coding: list = field(default_factory=list)
    llm_responses_balanced: list = field(default_factory=list)
    llm_responses_creative: list = field(default_factory=list)
    mcp_client: FakeMCPClient = field(init=False)
    prompt_config: FakePromptConfig = field(init=False)
    web_search: object = field(init=False)
    app_settings: FakeAppSettings = field(init=False)
    llm_strict: FakeLLMStrict = field(init=False)

    def __post_init__(self):
        self.mcp_client = FakeMCPClient(self.overview_text)
        self.prompt_config = FakePromptConfig(
            ["include_in_context", "get_skill_content", "web_search"]
        )
        self.web_search = object()
        self.app_settings = FakeAppSettings()
        self.llm_strict = FakeLLMStrict(self.llm_responses_strict)
        self.llm_coding = FakeLLMCoding(self.llm_responses_coding)
        self.llm_balanced = FakeLLMBalanced(self.llm_responses_balanced)
        self.llm_creative = FakeLLMCreative(self.llm_responses_creative)
