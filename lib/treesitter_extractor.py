from pathlib import Path
import re

from tree_sitter import Language, Parser, Node
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_go as tsgo

from lib.logger import get_logger

logger = get_logger(__name__)

LANGUAGES = {
    ".py": Language(tspython.language()),
    ".js": Language(tsjavascript.language()),
    ".jsx": Language(tsjavascript.language()),
    ".ts": Language(tstypescript.language_typescript()),
    ".tsx": Language(tstypescript.language_tsx()),
    ".go": Language(tsgo.language()),
}

SYMBOL_NODES = {
    ".py": {
        "class": ["class_definition"],
        "function": ["function_definition"],
    },
    ".js": {
        "class": ["class_declaration"],
        "function": ["function_declaration", "arrow_function"],
        "method": ["method_definition"],
    },
    ".jsx": {
        "class": ["class_declaration"],
        "function": ["function_declaration", "arrow_function"],
        "method": ["method_definition"],
    },
    ".ts": {
        "class": ["class_declaration"],
        "function": ["function_declaration"],
        "method": ["method_definition"],
        "interface": ["interface_declaration"],
        "type": ["type_alias_declaration"],
    },
    ".tsx": {
        "class": ["class_declaration"],
        "function": ["function_declaration", "arrow_function"],
        "method": ["method_definition"],
    },
    ".go": {
        "class": ["type_declaration"],
        "function": ["function_declaration"],
        "method": ["method_declaration"],
    },
}


def _get_signature_line(node: Node, code_bytes: bytes) -> str:
    for child in node.children:
        if child.type in ("block", "statement_block", "body", "class_body"):
            sig = code_bytes[node.start_byte : child.start_byte].decode("utf-8")
            sig = re.sub(r"\s*\n\s*", " ", sig).strip()  # collapse newlines
            sig = re.sub(r"\(\s+", "(", sig)  # remove space after (
            sig = re.sub(r",\s*\)", ")", sig)  # remove trailing comma before )
            return sig
    return (
        code_bytes[node.start_byte : node.end_byte]
        .decode("utf-8")
        .split("\n")[0]
        .strip()
    )


def _get_name(node: Node, code_bytes: bytes) -> str:
    for child in node.children:
        if child.type == "identifier":
            return code_bytes[child.start_byte : child.end_byte].decode("utf-8")
    return "<anonymous>"


def _walk(node: Node, code_bytes: bytes, ext: str, depth: int = 0) -> list[str]:
    lines = []
    indent = "  " * depth
    node_types = SYMBOL_NODES.get(ext, {})

    class_types = node_types.get("class", [])
    function_types = node_types.get("function", [])
    method_types = node_types.get("method", [])
    interface_types = node_types.get("interface", [])
    type_types = node_types.get("type", [])

    for child in node.children:
        if child.type in class_types:
            name = _get_name(child, code_bytes)
            lines.append(f"{indent}class {name}")
            lines.extend(_walk(child, code_bytes, ext, depth + 1))
        elif child.type in function_types:
            lines.append(f"{indent}{_get_signature_line(child, code_bytes)}")
        elif child.type in method_types:
            lines.append(f"{indent}{_get_signature_line(child, code_bytes)}")
        elif child.type in interface_types:
            name = _get_name(child, code_bytes)
            lines.append(f"{indent}interface {name}")
            lines.extend(_walk(child, code_bytes, ext, depth + 1))
        elif child.type in type_types:
            name = _get_name(child, code_bytes)
            lines.append(f"{indent}type {name}")
        else:
            lines.extend(_walk(child, code_bytes, ext, depth))

    return lines


def extract_signatures_from_content(file_path: str, content: str) -> str:
    """
    Public API — accepts file path (for extension detection) and
    content string (already fetched). Returns signature block or
    empty string for unsupported file types.
    """
    ext = Path(file_path).suffix
    if ext not in LANGUAGES:
        logger.warning(f"Tree sitter extension not supported {file_path}")
        return ""

    parser = Parser(LANGUAGES[ext])
    code_bytes = content.encode("utf-8")

    try:
        tree = parser.parse(code_bytes)
    except Exception:
        logger.warning(f"Tree sitter failed to parse {file_path}")
        return ""

    lines = _walk(tree.root_node, code_bytes, ext)
    return "\n".join(lines)


def chunk_file_content(file_path: str, content: str) -> list[dict]:
    ext = Path(file_path).suffix
    if ext not in LANGUAGES:
        logger.warning(f"Tree sitter extension not supported for chunking: {file_path}")
        return [{"name": "full_file", "type": "file", "content": content}]

    parser = Parser(LANGUAGES[ext])
    code_bytes = content.encode("utf-8")

    try:
        tree = parser.parse(code_bytes)
    except Exception:
        logger.warning(f"Tree sitter failed to parse for chunking: {file_path}")
        return [{"name": "full_file", "type": "file", "content": content}]

    node_types = SYMBOL_NODES.get(ext, {})
    class_types = node_types.get("class", [])
    function_types = node_types.get("function", [])

    chunks = []
    header_bytes = bytearray()

    for child in tree.root_node.children:
        is_chunkable = False
        chunk_type = ""

        if child.type in class_types:
            is_chunkable = True
            chunk_type = "class"
        elif child.type in function_types:
            is_chunkable = True
            chunk_type = "function"

        if is_chunkable:
            name = _get_name(child, code_bytes)
            chunk_content = code_bytes[child.start_byte : child.end_byte].decode(
                "utf-8"
            )
            chunks.append({"name": name, "type": chunk_type, "content": chunk_content})
        else:
            header_bytes.extend(code_bytes[child.start_byte : child.end_byte])
            header_bytes.extend(b"\n")

    header_content = header_bytes.decode("utf-8").strip()
    if header_content:
        chunks.insert(
            0, {"name": "module_header", "type": "header", "content": header_content}
        )

    return chunks
