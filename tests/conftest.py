from pathlib import Path
import pytest


@pytest.fixture
def mdfile():
    return Path(__file__).parent / "test.md"
