#!/usr/bin/python3

"""
Lists images referenced from one or more given markdown files.

This tool is mainly used for two different purposes:

With -l, it simply lists all images referenced from a markdown file. Use this,
e.g., to copy only relevant images::

    cp -p `md-images foo.md` ../some/new/folder

With -m, it can write Makefile dependency rules. Use this, e.g., in a Makefile
snippet as follows::

    Makefile.dep : $(MARKDOWN_FILES)
        md-images -d '%.pdf' $(MARKDOWN_FILES)

    include Makefile.dep

This will create and maintain and include a dependency file for all given
markdown files.
"""

from typing import List, Union
from urllib.parse import urlparse
from os import fspath

import panflute as pf
import argparse
from pathlib import Path


def load_markdown(markdown: Path) -> pf.Doc:
    return pf.convert_text(markdown.read_text(encoding='utf-8'), standalone=True)


def find_images(doc: pf.Doc) -> List[pf.Image]:
    images = []

    def add_image(elem, doc):
        if isinstance(elem, pf.Image):
            images.append(elem)

    doc.walk(add_image)
    return images


def resolve_url(url: str, markdown: Path) -> Union[Path, str]:
    parsed_url = urlparse(url)
    if parsed_url.scheme:  # absolute URI with scheme
        return url
    elif url.startswith('/'):  # absolute path
        return Path(url)
    else:
        return Path(markdown.parent, url)


def image_paths(markdown: Path) -> List[Union[Path, str]]:
    doc = load_markdown(markdown)
    images = find_images(doc)
    return [resolve_url(image.url, markdown) for image in images]


def deppattern(pattern: str, markdown: Path) -> str:
    if '%' in pattern:
        return pattern.replace('%', markdown.stem)
    else:
        return markdown.with_suffix(pattern)


def get_argparser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('markdown', nargs='+', help="Markdown files to read", type=Path)
    parser.add_argument('-d', '--suffix', action='append', metavar='suffix', help="""
        Write Makefile dependency rules for the given default suffix. Suffix may be either
        a filename extension or a string containing '%%'. If given multiple times, write
        multiple dependency rules.
    """)
    parser.add_argument('-i', '--individual-dependencies', nargs=1, metavar='suffix', help="""
        With -d, write dependencies for each markdown file to individual files with
        the given suffix.
    """)
    parser.add_argument('-l', '--list', action='store_true',
                        help="only list the dependent images")
    return parser


def _main():
    parser = get_argparser()
    options = parser.parse_args()

    rules = []
    imgs = set()
    for markdown in options.markdown:
        images = image_paths(markdown)
        imgs.update(images)
        if options.suffix:
            for suffix in options.suffix:
                rules.append(f'{deppattern(suffix, markdown)} : '
                             f'{markdown} {" ".join(map(fspath, images))}')
        else:
            rules.append(f'{markdown} : {" ".join(map(fspath, images))}')
        if options.individual_dependencies:
            with markdown.with_suffix(options.individual_dependencies).open('wt') as depfile:
                depfile.write('\n'.join(rules))
            rules = []

    if options.list:
        print("\n".join(map(str, imgs)))
    elif not options.individual_dependencies:
        print("\n".join(rules))


if __name__ == '__main__':
    _main()
