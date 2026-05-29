import re

from core.schemas import CodeChange, CodeChangeResponse
from lib.logger import get_logger

logger = get_logger(__name__)

TAG_NAME = "code_change"


def parse_code_changes(text: str, tag_name: str = TAG_NAME) -> CodeChangeResponse:
    change_pattern = re.compile(
        r"<" + tag_name + ">\s*"
        r"<file>(.*?)</file>\s*"
        r"<description>(.*?)</description>\s*"
        r"<old_text>(.*?)</old_text>\s*"
        r"<new_text>(.*?)</new_text>\s*"
        r"</" + tag_name + ">",
        re.DOTALL,
    )

    changes = []
    for match in change_pattern.finditer(text):
        file_path = match.group(1).strip()
        description = match.group(2).strip()
        old_text = match.group(3).strip(
            "\n"
        )  # preserve indentation, strip only newlines
        new_text = match.group(4).strip("\n")

        if not file_path:
            logger.warning(
                "Skipping malformed code_change block: missing file or old_text"
            )
            continue

        changes.append(
            CodeChange(
                file_path=file_path,
                description=description,
                old_text=old_text,
                new_text=new_text,
                is_new_file=not bool(old_text),
            )
        )

    # Summary = everything outside the <code_change> blocks
    summary = change_pattern.sub("", text).strip()
    if not summary:
        summary = (
            f"{len(changes)} code change(s) suggested."
            if changes
            else "No changes suggested."
        )

    logger.info("parse_code_changes: found %d change(s)", len(changes))
    return CodeChangeResponse(summary=summary, changes=changes)
