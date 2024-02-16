#!/usr/bin/python3

"""
Lists images referenced from one or more given markdown files,
optionally as makefile dependencies (-d) or as simple list (-l).
"""
from subprocess import check_call
import sys
from typing import List, TypeVar, Union, Type, Iterable
from urllib.parse import urlparse
from os import fspath

import panflute as pf
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory


def load_markdown(markdown: Path, input_format: str = None) -> pf.Doc:
    if input_format is None and markdown.suffix[1:] in pf.tools.RAW_FORMATS:
        input_format = markdown.suffix[1:]
    if input_format is None:
        input_format = "markdown"
    if input_format == "ipynb":
        return _load_notebook(markdown)
    return pf.convert_text(
        markdown.read_text(encoding="utf-8"), input_format=input_format, standalone=True
    )


def _load_notebook(notebook: Path) -> pf.Doc:
    with TemporaryDirectory() as tmp:
        from subprocess import run

        run(
            [
                "jupyter",
                "nbconvert",
                "--to",
                "html",
                "--output-dir",
                tmp,
                fspath(notebook),
            ],
            capture_output=True,
            check=True,
        )
        return load_markdown(Path(tmp, notebook.name).with_suffix(".html"), "html")


T = TypeVar("T", pf.Element, pf.Image)


def find_all(doc: pf.Doc, cls: Type[T]) -> List[T]:
    result = []

    def collect(elem: pf.Element, _):
        if isinstance(elem, cls):
            result.append(elem)

    doc.walk(collect)
    return result


def _is_generated_image(img: pf.Image) -> bool:
    try:
        classes = img.parent.parent.classes
        return "output" in classes
    except AttributeError:
        return False


def find_images(doc: pf.Doc, filter_outputs=True) -> List[pf.Image]:
    result = find_all(doc, pf.Image)
    if filter_outputs:
        result = [img for img in result if not _is_generated_image(img)]
    return result


def resolve_url(url: str, markdown: Path) -> Union[Path, str]:
    """
    Resolves an URL that has been found in the given source file.

    Args:
        url: the url to resolve
        markdown: source file, as a reference

    Returns:
        Path to the file, or the original str if it is an URL with a scheme:
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme:  # absolute URI with scheme
        return url
    elif url.startswith("/"):  # absolute path
        return Path(url)
    else:
        return Path(markdown.parent, url)


def image_paths(markdown: Path, include_urls: bool = False) -> List[Union[Path, str]]:
    """Returns all image paths of the given markdown file, resolved to the markdown file"""
    doc = load_markdown(markdown)
    images = find_images(doc)
    refs = [resolve_url(image.url, markdown) for image in images]
    return [ref for ref in refs if include_urls or isinstance(ref, Path)]


def deppattern(pattern: str, markdown: Path) -> Union[str, Path]:
    if "%" in pattern:
        return pattern.replace("%", markdown.stem)
    else:
        return markdown.with_suffix(pattern)


def unique(items: Iterable[T]) -> list[T]:
    result = []
    seen = set()
    for item in items:
        if repr(item) not in seen:
            result.append(item)
            seen.add(repr(item))
    return result


def list_urls(doc: pf.Doc, output_format="markdown") -> str:
    links = unique(find_all(doc, pf.Link))
    if output_format == "url":
        return "\n".join(link.url for link in links)
    elif output_format == "tabbed":
        return "\n".join(link.url + "\t" + pf.stringify(link) for link in links)
    else:
        items = [pf.ListItem(pf.Plain(link)) for link in links]
        bullet_list = pf.BulletList()
        bullet_list.content.extend(items)
        return pf.convert_text(
            bullet_list, input_format="panflute", output_format=output_format
        )


def get_argparser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", nargs="+", help="Markdown files to read", type=Path)
    parser.add_argument(
        "-d",
        "--suffix",
        action="append",
        metavar="suffix",
        help="""
        Write Makefile dependency rules for the given default suffix. Suffix may be either
        a filename extension or a string containing '%%'. If given multiple times, write
        multiple dependency rules.
    """,
    )
    parser.add_argument(
        "-i",
        "--individual-dependencies",
        nargs=1,
        metavar="suffix",
        help="""
        With -d, write dependencies for each markdown file to individual files with
        the given suffix.
    """,
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="only list the dependent images"
    )
    parser.add_argument(
        "-u",
        "--urls",
        nargs="?",
        metavar="url_format",
        const="tabbed",
        help="Extract all links. The optional format is the output format,"
        "legal values include tabbed (url + tab + text, the default),"
        "url (only the url), and supported pandoc output formats.",
    )
    #    parser.add_argument('-c', '--copy', nargs=1, metavar='target', type=Path,
    #                        help="copy markdown and images to the given target directory")
    parser.add_argument(
        "-f",
        "--format",
        nargs=1,
        help="Format of the source files. Default is to autodetect and fallback to markdown.",
    )
    parser.add_argument(
        "-k", "--keep-going", action="store_true", help="do not quit on errors"
    )
    parser.add_argument(
        "-V",
        "--variants",
        action="store_true",
        help="Add variants with different suffix if they exist",
    )
    return parser


def add_variants(images: Iterable[Path]) -> list[Path]:
    result = []
    for orig in images:
        result.append(orig)
        result.extend(orig.parent.glob(orig.stem + ".*"))
    return result


def _main():
    parser = get_argparser()
    options = parser.parse_args()

    rules = []
    imgs = set()
    for markdown in options.markdown:
        try:
            if options.urls:
                doc = load_markdown(markdown, options.format)
                print(list_urls(doc, options.urls))
                continue

            images = image_paths(markdown)
            imgs.update(images)
            if options.variants:
                imgs.update(add_variants(imgs))

            if options.suffix:
                for suffix in options.suffix:
                    rules.append(
                        f"{deppattern(suffix, markdown)} : "
                        f'{markdown} {" ".join(map(fspath, images))}'
                    )
            else:
                rules.append(f'{markdown} : {" ".join(map(fspath, images))}')
            if options.individual_dependencies:
                with markdown.with_suffix(options.individual_dependencies).open(
                    "wt"
                ) as depfile:
                    depfile.write("\n".join(rules))
                rules = []
        except Exception as e:
            if options.keep_going:
                msg = f"ERROR analyzing {markdown}: {e}"
                rules.append("# " + msg)
                print(msg, file=sys.stderr)
            else:
                raise

    if options.list:
        print("\n".join(map(str, imgs)))
    elif not options.individual_dependencies:
        print("\n".join(rules))


if __name__ == "__main__":
    _main()
