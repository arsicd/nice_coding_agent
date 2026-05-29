from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class PlanResponse(BaseModel):
    summary: str
    loaded_files: list[str] = Field(default_factory=list)


class ContentType(str, Enum):
    file = "file"
    web_search = "web_search"
    project_overview = "project_overview"
    skill = "skill"
    general = "general"


class ContextItem(BaseModel):
    title: str
    content: str
    type: ContentType


class CodeChange(BaseModel):
    file_path: str = Field(
        description="Relative path to the file to be created or modified."
    )
    description: str = Field(description="Short explanation of what this change does.")
    old_text: str = Field(
        default="",
        description="Exact verbatim code to be replaced, including all whitespace and indentation. Leave empty when creating a new file.",
    )
    new_text: str = Field(
        default="",
        description="Replacement code or full new file content.",
    )
    is_new_file: bool = Field(default=False, exclude=True)


class CodeChangeResponse(BaseModel):
    summary: str = Field(description="A brief summary of the overall changes.")
    changes: list[CodeChange] = Field(
        default_factory=list,
        description="List of individual file changes. Each change represents one logical modification or new file.",
    )


class StateInfo(BaseModel):
    context: str
    instructions: str
    implementation: CodeChangeResponse | None


class SearchResult(BaseModel):
    content: str
    source: str
    score: float

    model_config = ConfigDict(from_attributes=True)


class StreamKind(str, Enum):
    START = "start"
    TEXT = "text"
    REASONING = "reasoning"
    END = "end"


class StreamEvent(BaseModel):
    delta: str
    kind: StreamKind = StreamKind.TEXT
    can_stop: bool
