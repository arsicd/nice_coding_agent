from dataclasses import dataclass, field


@dataclass
class ContextEntry:
    id: str
    label: str
    content: str
    raw_content: str = field(default="")
    is_loading: bool = False
    editable: bool = field(default=True)
    is_minimized: bool = field(default=False)
    pinned: bool = field(default=False)
    render_as_markdown: bool = field(default=False)
    is_editing: bool = field(default=False)

    def is_file_entry(self) -> bool:
        """Heuristic: entries whose label starts with the 📄 file glyph."""
        return self.label.startswith("📄")

    def file_path_from_label(self) -> str:
        return self.label.replace("📄", "", 1).strip()

    def file_extension(self) -> str:
        path = self.file_path_from_label()
        leaf = path.rsplit("/", 1)[-1]
        return leaf.rsplit(".", 1)[-1].lower() if "." in leaf else ""

    def file_content_md(self, raw_content: str) -> str:
        file_ext = self.file_extension()
        return f"```{file_ext}\n{raw_content}\n```"
