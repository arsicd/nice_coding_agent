from lib.tree_parser import all_tree_files, format_tree_as_text, parse_tree_to_nodes


def get_tree_nodes() -> list[dict]:
    return [
        {
            "id": "src",
            "label": "src/",
            "icon": "folder",
            "is_folder": True,
            "children": [
                {
                    "id": "src/app.py",
                    "label": "app.py",
                    "icon": "insert_drive_file",
                    "is_folder": False,
                    "children": [],
                },
                {
                    "id": "src/utils",
                    "label": "utils/",
                    "icon": "folder",
                    "is_folder": True,
                    "children": [
                        {
                            "id": "src/utils/helper.py",
                            "label": "helper.py",
                            "icon": "insert_drive_file",
                            "is_folder": False,
                            "children": [],
                        }
                    ],
                },
            ],
        },
        {
            "id": "README.md",
            "label": "README.md",
            "icon": "insert_drive_file",
            "is_folder": False,
            "children": [],
        },
    ]


def test_parse_tree_to_nodes_from_plain_tree_text():
    tree_text = """.
├── src/
│   ├── app.py
│   └── utils/
│       └── helper.py
└── README.md
"""

    nodes = parse_tree_to_nodes(tree_text)

    assert nodes == get_tree_nodes()


def test_parse_tree_to_nodes_from_json_tree_payload():
    tree_text = '{"tree": ".\n├── docs/\n│   └── guide.md\n└── pyproject.toml\n"}'

    nodes = parse_tree_to_nodes(tree_text)

    assert nodes[0]["id"] == "docs"
    assert nodes[0]["children"][0]["id"] == "docs/guide.md"
    assert nodes[1]["id"] == "pyproject.toml"


def test_all_tree_files_returns_only_file_ids():
    tree_nodes = get_tree_nodes()

    assert all_tree_files(tree_nodes) == [
        "src/app.py",
        "src/utils/helper.py",
        "README.md",
    ]


def test_format_tree_as_text_round_trips_tree_structure():
    tree_nodes = get_tree_nodes()

    assert format_tree_as_text(tree_nodes) == (
        "├── src/\n"
        "│   ├── app.py\n"
        "│   └── utils/\n"
        "│       └── helper.py\n"
        "└── README.md"
    )
