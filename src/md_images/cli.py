import builtins
from pathlib import Path
from typing import Annotated, Literal
from panflute import (
    BulletList,
    Doc,
    Header,
    Inline,
    Link,
    ListItem,
    Plain,
    Str,
    convert_text,
    stringify,
)
from rich.console import Console
from rich.syntax import Syntax
from rich.logging import RichHandler

from cyclopts import App, Parameter

from md_images.core import relative_fspath

from .model import MdFile, SourceSelection
from .core import find_all

import logging

console = Console()


def print(*args, **kwargs):
    if console.is_terminal:
        console.print(*args, **kwargs)
    else:
        builtins.print(*args, **kwargs)


logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(message)s", handlers=[RichHandler(show_time=False)], level=logging.INFO
)

app = App(default_parameter=Parameter(negative=[]), help_format="rst")


Texts = Annotated[
    list[Path],
    Parameter(
        negative=[],
        help="Text file(s) to analyze. May be anything pandoc can read.",
    ),
]

Select = Annotated[
    SourceSelection, Parameter(["-s", "--select"], help=SourceSelection.__doc__)
]


@app.command
def ls(texts: Texts, /, *, select: Select = SourceSelection.EXPLICIT):
    """List image files included in the given text files"""
    all_images = set()
    for text in texts:
        source = MdFile(text)
        all_images.update(source.image_sources(select))
    print("\n".join(relative_fspath(img) for img in all_images))


@app.command
def dep(
    texts: Texts,
    /,
    *,
    suffix: Annotated[
        list[str] | None,
        Parameter(
            [
                "-d",
                "--suffix",
            ]
        ),
    ] = None,
    individual_dependencies: Annotated[
        str | None, Parameter(["-i", "--individual-dependencies"])
    ] = None,
):
    """
    Print makefile rules for the given text files.

    Args:
        texts: file or files to analyze. Can actually be anything pandoc is able to read, not only markdown files.
        suffix: suffix for the target rules in the makefile. If you provide multiple suffixes separated by space, a rule will be created for each suffix. You can also provide a pattern using '%'
        individual_dependencies: if provided, write an individual dependenca file with the given suffix for each source file
    """
    for text in texts:
        source = MdFile(text)
        rules = "\n".join([source.rule(suf) for suf in suffix or []] or [source.rule()])
        if individual_dependencies:
            text.with_suffix(individual_dependencies).write_text(rules + "\n")
        else:
            print(rules)


@app.command
def cp(
    texts: Texts,
    target: Path,
    /,
    select: Select = SourceSelection.SOURCE,
):
    """
    Copy text files including linked image files to the given target.

    If a single source file is provided and the target is not an existing directory,
    it is interpreted as the target file name, otherwise it is thought to be a directory.
    All neccessery directories are created if they do not exist.
    """
    if target.is_dir():
        target_dir = target
    elif len(texts) > 1 and not target.exists():
        target_dir = target
        if target.suffixes:
            logger.warning(
                "Since multiple sources are provided, %s is created as a directory",
                target_dir,
            )
    else:
        target_dir = target.parent

    target_dir.mkdir(parents=True, exist_ok=True)
    for text in texts:
        source = MdFile(text)
        if target_dir == target:
            dest = target_dir / text.name
        else:
            dest = target
        source.copy(dest, select)


@app.command
def links(
    texts: Texts,
    /,
    format: Annotated[
        Literal["tabbed", "url"] | str, Parameter(["-f", "--format"])
    ] = "tabbed",
):
    """
    List all links in the given text file.

    Args:
        format: output format. "tabbed" (default) generates a TSV table
                of source, URL and title, "url" generates a list of URLs only.
                Additionally, you can pass any format pandoc is able to
                generate.
    """
    result = []
    for text in texts:
        doc = MdFile(text).doc
        title = doc.get_metadata("title") or text.stem
        links: list[Link] = find_all(doc, Link)  # type: ignore
        if format == "url":
            result.extend(link.url for link in links)
        elif format == "tabbed":
            result.extend(
                "\t".join([str(text), link.url, stringify(link)]) for link in links
            )
        else:
            items = [ListItem(Plain(link)) for link in links]
            bullet_list = BulletList()
            bullet_list.content.extend(items)
            result.append(Header(Link(Str(title), url=str(text)), level=2))
            result.append(bullet_list)

    if format == "tabbed" or format == "url":
        print("\n".join(result))
    else:
        print(
            Syntax(
                convert_text(result, input_format="panflute", output_format=format),
                format,
            )
        )


@app.default
def md_images(
    markdown: list[Path],
    /,
    *,
    list_: Annotated[bool, Parameter(["-l", "--list"], negative=[])] = False,
    suffix: Annotated[
        list[str] | None, Parameter(["-d", "--suffix"], negative=[])
    ] = None,
    individual_dependencies: Annotated[
        str | None, Parameter(["-i", "--individual-dependencies"])
    ] = None,
):
    """
    Analyze the listed markdown files for images.

    Args:
        markdown: file or files to analyze. Can actually be anything pandoc is able to read, not only markdown files.
        suffix: suffix for the target rules in the makefile. If you provide multiple suffixes, a rule will be created for each suffix.

    """
    all_dependencies = set()
    for source_file in markdown:
        source = MdFile(source_file)
        if list_:
            all_dependencies.update(source.image_paths)
        else:
            rules = "\n".join(
                [source.rule(suf) for suf in suffix or []] or [source.rule()]
            )
            if individual_dependencies:
                source_file.with_suffix(individual_dependencies).write_text(
                    rules + "\n"
                )
            else:
                if console.is_terminal:
                    console.print(Syntax(rules, "Makefile", word_wrap=True))
                else:
                    print(rules)
