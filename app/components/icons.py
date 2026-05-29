"""Inline SVG icon strings for the dark IDE theme.

Each function returns a string of `<svg>...</svg>` markup with `currentColor`
strokes so colors are driven by CSS (`color: var(--c-...)` on a parent class).
Designed to be embedded via `ui.html(icon_xxx())`.
"""

_BASE = (
    'xmlns="http://www.w3.org/2000/svg" fill="none" '
    'stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"'
)


def chevron_right(size: int = 10) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.4" {_BASE}>'
        '<polyline points="6,4 10,8 6,12"/></svg>'
    )


def folder(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M2 5a1 1 0 0 1 1-1h3.6l1.4 1.4H13a1 1 0 0 1 1 1V12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5z"/>'
        "</svg>"
    )


def file_icon(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M4 2h5l3 3v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/>'
        '<polyline points="9,2 9,5 12,5"/>'
        "</svg>"
    )


def plus(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.3" {_BASE}>'
        '<line x1="8" y1="3" x2="8" y2="13"/>'
        '<line x1="3" y1="8" x2="13" y2="8"/>'
        "</svg>"
    )


def minus(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.3" {_BASE}>'
        '<line x1="3" y1="8" x2="13" y2="8"/>'
        "</svg>"
    )


def maximize(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.3" {_BASE}>'
        '<rect x="3" y="3" width="10" height="10" rx="1"/>'
        "</svg>"
    )


def close(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.3" {_BASE}>'
        '<line x1="4" y1="4" x2="12" y2="12"/>'
        '<line x1="12" y1="4" x2="4" y2="12"/>'
        "</svg>"
    )


def pin(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M9.5 2 14 6.5l-3 1L8 11 5 8l3.5-3 1-3z"/>'
        '<line x1="5" y1="8" x2="2" y2="14"/>'
        "</svg>"
    )


def refresh(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.2" {_BASE}>'
        '<path d="M3 8a5 5 0 0 1 8.5-3.5L13 6"/>'
        '<polyline points="13,3 13,6 10,6"/>'
        '<path d="M13 8a5 5 0 0 1-8.5 3.5L3 10"/>'
        '<polyline points="3,13 3,10 6,10"/>'
        "</svg>"
    )


def collapse(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.3" {_BASE}>'
        '<rect x="2.5" y="3" width="11" height="10" rx="1"/>'
        '<line x1="6" y1="3" x2="6" y2="13"/>'
        "</svg>"
    )


def add_to_context(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.3" {_BASE}>'
        '<line x1="2" y1="8" x2="11" y2="8"/>'
        '<polyline points="8,5 11,8 8,11"/>'
        '<line x1="13.5" y1="3.5" x2="13.5" y2="12.5"/>'
        "</svg>"
    )


def add_overview_to_context(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.2" {_BASE}>'
        '<rect x="2.5" y="3" width="8.5" height="10" rx="1"/>'
        '<line x1="2.5" y1="6.5" x2="11" y2="6.5"/>'
        '<line x1="5" y1="9.5" x2="8.5" y2="9.5"/>'
        '<line x1="5" y1="11.5" x2="7.5" y2="11.5"/>'
        '<line x1="13.2" y1="5" x2="13.2" y2="11"/>'
        '<line x1="10.2" y1="8" x2="15.2" y2="8"/>'
        "</svg>"
    )


def search(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.2" {_BASE}>'
        '<circle cx="7" cy="7" r="4"/>'
        '<line x1="10" y1="10" x2="13" y2="13"/>'
        "</svg>"
    )


def sparkle(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M8 2 9.2 6.8 14 8l-4.8 1.2L8 14l-1.2-4.8L2 8l4.8-1.2L8 2z"/>'
        "</svg>"
    )


def edit(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M3 11.5V13h1.5L12 5.5 10.5 4 3 11.5z"/>'
        '<path d="M9.5 4.5 11 3l2 2-1.5 1.5"/>'
        "</svg>"
    )


def doc(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M4 2h5l3 3v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/>'
        '<line x1="5" y1="8" x2="11" y2="8"/>'
        '<line x1="5" y1="10.5" x2="11" y2="10.5"/>'
        "</svg>"
    )


def tools(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M11 2 9 4l3 3 2-2-3-3z"/>'
        '<line x1="9" y1="4" x2="3" y2="10"/>'
        '<path d="M3 10v3h3l6-6"/>'
        "</svg>"
    )


def chat(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M3 4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H6l-3 3V4z"/>'
        "</svg>"
    )


def overview(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.2" {_BASE}>'
        '<rect x="2.5" y="3" width="11" height="10" rx="1"/>'
        '<line x1="2.5" y1="6.5" x2="13.5" y2="6.5"/>'
        '<line x1="5" y1="9.5" x2="11" y2="9.5"/>'
        '<line x1="5" y1="11.5" x2="9" y2="11.5"/>'
        "</svg>"
    )


def layers(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<polygon points="8,2 14,5 8,8 2,5"/>'
        '<polyline points="2,8 8,11 14,8"/>'
        '<polyline points="2,11 8,14 14,11"/>'
        "</svg>"
    )


def check(size: int = 11) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.6" {_BASE}>'
        '<polyline points="3,8 7,12 13,4"/>'
        "</svg>"
    )


def bolt(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'fill="currentColor" stroke="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M9 1 3 9h4l-1 6 6-8H8l1-6z"/>'
        "</svg>"
    )


def settings(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<circle cx="8" cy="8" r="2"/>'
        '<path d="M13.5 7.5c-.2-.5-.5-1-.8-1.4l.6-1.6-1.4-1.4-1.6.6c-.4-.3-.9-.6-1.4-.8V1.5h-2v1.4c-.5.2-1 .5-1.4.8l-1.6-.6-1.4 1.4.6 1.6c-.3.4-.6.9-.8 1.4H1.5v2h1.4c.2.5.5 1 .8 1.4l-.6 1.6 1.4 1.4 1.6-.6c.4.3.9.6 1.4.8v1.4h2v-1.4c.5-.2 1-.5 1.4-.8l1.6.6 1.4-1.4-.6-1.6c.3-.4.6-.9.8-1.4h1.4v-2h-1.4z"/>'
        "</svg>"
    )


def branch(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<circle cx="4" cy="3.5" r="1.5"/>'
        '<circle cx="4" cy="12.5" r="1.5"/>'
        '<circle cx="12" cy="6" r="1.5"/>'
        '<line x1="4" y1="5" x2="4" y2="11"/>'
        '<path d="M12 7.5v.5a3 3 0 0 1-3 3H7"/>'
        "</svg>"
    )


def send(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.2" {_BASE}>'
        '<polygon points="2,8 14,2 9,14 7,9"/>'
        "</svg>"
    )


def copy(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<rect x="5" y="5" width="9" height="9" rx="1"/>'
        '<path d="M11 5V3a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h2"/>'
        "</svg>"
    )


def trash(size: int = 12) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<polyline points="2.5,4 13.5,4"/>'
        '<path d="M5 4V2.5A1 1 0 0 1 6 1.5h4a1 1 0 0 1 1 1V4"/>'
        '<path d="M3.5 4l.5 9a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l.5-9"/>'
        "</svg>"
    )


def diagonal(size: int = 11) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.2" {_BASE}>'
        '<polyline points="9,3 13,3 13,7"/>'
        '<polyline points="7,13 3,13 3,9"/>'
        '<line x1="13" y1="3" x2="9" y2="7"/>'
        '<line x1="3" y1="13" x2="7" y2="9"/>'
        "</svg>"
    )


def stop(size: int = 11) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        'fill="currentColor" stroke="none" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="3" y="3" width="10" height="10" rx="1"/>'
        "</svg>"
    )


def bug(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<rect x="5" y="5" width="6" height="8" rx="3"/>'
        '<line x1="2" y1="9" x2="5" y2="9"/>'
        '<line x1="11" y1="9" x2="14" y2="9"/>'
        '<line x1="3" y1="6" x2="5.5" y2="7"/>'
        '<line x1="13" y1="6" x2="10.5" y2="7"/>'
        '<line x1="3" y1="12" x2="5.5" y2="11"/>'
        '<line x1="13" y1="12" x2="10.5" y2="11"/>'
        '<path d="M6 5a2 2 0 0 1 4 0"/>'
        "</svg>"
    )


def eye(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M1.5 8s2.5-4.5 6.5-4.5S14.5 8 14.5 8s-2.5 4.5-6.5 4.5S1.5 8 1.5 8z"/>'
        '<circle cx="8" cy="8" r="2"/>'
        "</svg>"
    )


def web(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<circle cx="7.5" cy="7.5" r="5.5"/>'
        '<line x1="2" y1="7.5" x2="13" y2="7.5"/>'
        '<path d="M7.5 2c2.5 3 2.5 8 0 11"/>'
        '<path d="M7.5 2c-2.5 3-2.5 8 0 11"/>'
        '<line x1="11.2" y1="11.2" x2="14" y2="14" stroke-width="1.4"/>'
        "</svg>"
    )


def skill(size: int = 13) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 16 16" '
        f'stroke-width="1.1" {_BASE}>'
        '<path d="M3 5a3 3 0 0 1 6 0v6a2 2 0 1 1-4 0V5"/>'
        '<path d="M9 8h3a2 2 0 0 1 0 4h-1"/>'
        "</svg>"
    )


_EXT_CLASS_MAP = {
    "py": "ext-py",
    "md": "ext-md",
    "mdx": "ext-md",
    "txt": "ext-md",
    "rst": "ext-md",
    "env": "ext-env",
    "toml": "ext-cfg",
    "yaml": "ext-cfg",
    "yml": "ext-cfg",
    "json": "ext-cfg",
    "ini": "ext-cfg",
    "cfg": "ext-cfg",
    "lock": "ext-cfg",
    "js": "ext-js",
    "ts": "ext-js",
    "jsx": "ext-js",
    "tsx": "ext-js",
    "mjs": "ext-js",
    "cjs": "ext-js",
}


def file_ext_class(name: str) -> str:
    """CSS class for a filename's extension tint, or empty string."""
    n = name.lower().lstrip(".")
    if "." not in name and "env" in n:
        return "ext-env"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return _EXT_CLASS_MAP.get(ext, "")
