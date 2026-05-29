import json


def parse_tree_to_nodes(tree_text: str, excluded: list[str] = None) -> list[dict]:
    if not excluded:
        excluded = []

    try:
        data = json.loads(tree_text)
        tree_text = data.get("tree", tree_text)
    except (json.JSONDecodeError, TypeError):
        pass

    nodes = []
    stack = []
    lines = tree_text.splitlines()

    indents = []
    for line in lines[1:]:
        if not line.strip():
            continue
        clean = (
            line.replace("├── ", "    ")
            .replace("└── ", "    ")
            .replace("│   ", "    ")
            .replace("│", " ")
        )
        indents.append(len(clean) - len(clean.lstrip()))
    base_indent = min(indents) if indents else 4

    # Track which indent levels are inside an excluded directory
    excluded_levels: set[int] = set()

    for raw_line in lines[1:]:
        if not raw_line.strip():
            continue
        clean = (
            raw_line.replace("├── ", "    ")
            .replace("└── ", "    ")
            .replace("│   ", "    ")
            .replace("│", " ")
        )
        indent = len(clean) - len(clean.lstrip())
        level = (indent - base_indent) // 4

        name = raw_line.strip()
        for ch in ["├── ", "└── ", "│   ", "│"]:
            name = name.replace(ch, "")
        name = name.strip()
        if not name:
            continue

        # Prune excluded_levels set
        excluded_levels = {lvl for lvl in excluded_levels if lvl < level}
        if excluded_levels:
            continue

        is_dir = name.endswith("/")
        bare_name = name.rstrip("/")

        if bare_name in excluded:
            excluded_levels.add(level)
            continue

        # ✅ Pop FIRST, THEN read parent
        while stack and stack[-1][0] >= level:
            stack.pop()

        parent_path = stack[-1][1]["id"] if stack else ""
        full_id = f"{parent_path}/{bare_name}" if parent_path else bare_name

        node = {
            "id": full_id,
            "label": name,
            "icon": "folder" if is_dir else "insert_drive_file",
            "is_folder": is_dir,
            "children": [] if is_dir else [],
        }

        if stack:
            parent = stack[-1][1]
            if parent.get("children") is None:
                parent["children"] = []
            parent["children"].append(node)
        else:
            nodes.append(node)

        if is_dir:
            stack.append((level, node))

    return nodes


def all_tree_files(tree_nodes: list[dict]) -> list[str]:
    files: list[str] = []

    def _walk(nodes: list[dict], indent: int = 0) -> None:
        for node in nodes:
            if not node["is_folder"]:
                files.append(node["id"])
            if node.get("is_folder") and node.get("children"):
                _walk(node["children"], indent + 1)

    _walk(tree_nodes)
    return files


def format_tree_as_text(tree_nodes: list[dict]) -> str:
    lines: list[str] = []

    def _walk(nodes: list[dict], prefix: str = "") -> None:
        for i, node in enumerate(nodes):
            is_last = i == len(nodes) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{node['label']}")
            if node.get("is_folder") and node.get("children"):
                extension = "    " if is_last else "│   "
                _walk(node["children"], prefix + extension)

    _walk(tree_nodes)
    return "\n".join(lines)
