from pathlib import Path

import pytest

from md_images import load_markdown, resolve_url
from md_images.core import deppattern, unique
import panflute as pf


def test_load(mdfile):
    assert isinstance(load_markdown(mdfile), pf.Doc)

def test_resolve_rel(mdfile):
    """Relative paths are resolved to a Path object relative to the mdfile"""
    url = "example.svg"
    assert resolve_url(url, mdfile) == mdfile.parent / "example.svg"

def test_resolve_abs(mdfile):
    """Absolute paths are resolved to a Path object"""
    url = "/tmp/example.svg"
    assert resolve_url(url, mdfile) == Path(url)

def test_resolve_url(mdfile):
    """URLs with a scheme are left alone"""
    url = "https://example.com/example.svg"
    assert resolve_url(url, mdfile) == url

@pytest.mark.parametrize("pattern,expected", [
    (".pdf", "test.pdf"),
    ("%-ol.pdf", "test-ol.pdf"),
])
def test_deppattern(pattern, expected):
    assert str(deppattern(pattern, Path("test.md"))) == expected

def test_unique():
    assert unique([]) == []
    assert unique([1, 2, 3]) == [1, 2, 3]
    assert unique([3, 2, 3]) == [3, 2]