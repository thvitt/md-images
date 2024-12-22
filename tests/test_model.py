from os import chdir

import pytest
from md_images.model import MdFile, SourceSelection


@pytest.fixture
def mdobject(mdfile):
    return MdFile(mdfile)

def test_str(mdfile, mdobject):
    assert str(mdobject) == f"{mdfile} (Test file)"

def test_image_urls(mdobject):
    assert mdobject.image_urls == {"example.png"}

def test_image_paths(mdobject):
    expected = mdobject.path.parent / "example.png"
    assert mdobject.image_paths == {expected}

def test_image_sources(mdobject):
    assert mdobject.image_sources(SourceSelection.SOURCE) == {mdobject.path.parent / "example.svg"}
    assert mdobject.image_sources(SourceSelection.BOTH) == {
        mdobject.path.parent / "example.svg",
        mdobject.path.parent / "example.png",
    }


def test_rules(mdobject):
    chdir(mdobject.path.parent)
    assert (
        mdobject.rule()
        == "test.md : example.png"
    )

def test_rules_percent(mdobject):
    assert (
            mdobject.rule("%-ol.pdf", base=mdobject.path.parent)
            == "test-ol.pdf : test.md example.png"
    )


def test_rules_suffix(mdobject):
    assert (
            mdobject.rule(".pdf", base=mdobject.path.parent)
            == "test.pdf : test.md example.png"
    )

def test_copy(mdobject, tmp_path):
    mdobject.copy(tmp_path)
    svg = tmp_path / "example.svg"
    assert svg.exists()
    assert svg.is_file()

def test_copy_selection(mdobject, tmp_path):
    target = tmp_path / "foo.md"
    mdobject.copy(target, selection=SourceSelection.EXPLICIT)
    img = tmp_path / "example.png"
    assert img.exists()
    assert img.is_file()
