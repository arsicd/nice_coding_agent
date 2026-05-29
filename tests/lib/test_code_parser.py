import textwrap

from lib.code_parser import parse_code_changes


def test_parse_code_changes_happy_path():
    text = textwrap.dedent(
        """
        Some summary text before the change.

        <code_change>
            <file>lib/example.py</file>
            <description>Update example implementation</description>
            <old_text>
        old line
            </old_text>
            <new_text>
        new line
            </new_text>
        </code_change>

        Some summary text after the change.
        """
    )

    result = parse_code_changes(text)

    assert result.summary == "Some summary text before the change.\n\n\n\nSome summary text after the change."
    assert len(result.changes) == 1

    change = result.changes[0]
    assert change.file_path == "lib/example.py"
    assert change.description == "Update example implementation"
    assert change.old_text == "old line\n    "
    assert change.new_text == "new line\n    "
    assert change.is_new_file is False
