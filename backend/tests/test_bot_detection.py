import pytest

from app.bot_detection import is_bot


@pytest.mark.parametrize(
    "user_agent, expected",
    [
        (None, True),
        ("", True),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0", False),
        ("Slackbot-LinkExpanding 1.0", True),
        ("curl/8.4.0", True),
        ("python-requests/2.31", True),
    ],
)
def test_is_bot(user_agent, expected):
    assert is_bot(user_agent) is expected
