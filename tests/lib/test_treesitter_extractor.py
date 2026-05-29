from lib.treesitter_extractor import extract_signatures_from_content


def test_extract_signatures_from_content_happy_path():
    content = """
class Greeter:
    def say_hello(self, name):
        return f"Hello {name}"


def add(a, b):
    return a + b
"""

    result = extract_signatures_from_content("example.py", content)

    assert result == "class Greeter\n  def say_hello(self, name):\ndef add(a, b):"
