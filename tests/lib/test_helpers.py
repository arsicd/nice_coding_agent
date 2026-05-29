from langchain_core.messages import AIMessage

from lib.helpers import extract_text_response


def test_extract_text_response_returns_latest_text_content():
    messages = [
        AIMessage(content="   "),
        AIMessage(
            content=[
                {"type": "image", "url": "https://example.com/image.png"},
                {"type": "text", "text": "  Hello  "},
            ]
        ),
    ]

    assert extract_text_response(messages) == "Hello"
