import pytest
from pydantic import ValidationError

from app.schemas import LinkCreateRequest


def test_reject_blank_url_rejects_whitespace_string():
    with pytest.raises(ValidationError):
        LinkCreateRequest(long_url="   ")


def test_reject_blank_url_rejects_empty_string():
    with pytest.raises(ValidationError):
        LinkCreateRequest(long_url="")


def test_valid_url_is_accepted():
    req = LinkCreateRequest(long_url="https://example.com")
    assert str(req.long_url) == "https://example.com/"
