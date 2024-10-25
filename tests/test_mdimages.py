from pathlib import Path

import panflute as pf
import pytest

import md_images as mdi
from posix import fspath


@pytest.fixture
def mdfile():
    return Path(__file__).parent / "test.md"


@pytest.fixture
def mddoc(mdfile):
    return mdi.load_markdown(mdfile)


def test_load_markdown(mddoc):
    doc = mddoc
    assert isinstance(doc, pf.Doc)


def test_find_images(mddoc):
    doc = mddoc
    images = mdi.find_images(doc)
    assert len(images) == 1
    assert images[0].url == "example.png"


def test_find_url(mddoc):
    doc = mddoc
    links = mdi.find_all(doc, pf.Link)
    assert links[0].url == "https://example.com"


def test_resolve(mdfile):
    resolved = mdi.resolve_url("example.svg", mdfile)
    assert Path(resolved).exists()


def test_image_paths(mdfile):
    paths = mdi.image_paths(mdfile)
    fspaths = [fspath(p.relative_to(mdfile.parent.absolute())) for p in paths]
    assert fspaths == ["example.png"]
