import shlex
from pathlib import Path
from subprocess import run as run_


def run(cmdline: str):
    args = shlex.split(cmdline)
    return run_(args, cwd=Path(__file__).parent, capture_output=True, encoding="utf-8")


def test_mdimages_help():
    result = run("md-images --help")
    assert result.returncode == 0
    assert result.stdout.startswith("usage: md-images")


def test_list_images():
    result = run("md-images -l test.md")
    assert result.returncode == 0
    assert result.stdout == "example.png\n"


def test_list_rules():
    result = run("md-images -d .pdf test.md")
    assert result.returncode == 0
    assert result.stdout == "test.pdf : test.md example.png\n"
