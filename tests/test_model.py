import pytest
from md_images.model import MdFile


@pytest.fixture
def mdobject(mdfile):
    return MdFile(mdfile)


def test_image_urls(mdobject):
    assert mdobject.image_urls == {"example.png"}


def test_image_paths(mdobject):
    expected = mdobject.path.parent / "example.png"
    assert mdobject.image_paths == {expected}


def test_rules(mdobject):
    assert (
        mdobject.rule(".pdf", base=mdobject.path.parent)
        == "test.pdf : test.md example.png"
    )


def test_copy(mdobject, tmp_path):
    mdobject.copy(tmp_path)
    svg = tmp_path / "example.svg"
    assert svg.exists()
    assert svg.is_file()
