#!/usr/bin/python3

"""
Lists images referenced from one or more given markdown files,
optionally as makefile dependencies (-d) or as simple list (-l).
"""

import argparse
from os import fspath
from pathlib import Path

from panflute.utils import sys

from md_images.core import (
    add_variants,
    deppattern,
    image_paths,
    list_urls,
    load_markdown,
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
