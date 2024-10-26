from collections.abc import Iterable
from posix import fspath
from collections import defaultdict
from pathlib import Path
from typing import Callable, Literal
import cyclopts
from shlex import join, quote

app = cyclopts.App()


class SuffixRanks:

    default_preferences = ".ipynb .md .uml .dot .svg .tex".split()

    def __init__(self, preferences: list[str] | None = None):
        self.preferences = preferences or self.default_preferences
        self.ranks = {
            suffix: rank for rank, suffix in enumerate(self.preferences, start=1)
        }

    def __call__(self, file: Path) -> int:
        return self.ranks.get(file.suffix, len(self.ranks) + 1)


def rank_variants(
    files: Iterable[Path],
    find_variants: bool = False,
    ranker: Callable[[Path], int] | None = None,
) -> dict[Path, list[Path]]:
    """
    Group the given list of files by base name and rank the variants by suffix.

    Args:
        files: List of files to consider.
        find_variants: If true, look for all files on disk matching foo.*, not only those listed.
        ranker: A function that assigns a rank to a file.

    Returns:
        A dictionary mapping base names to a list of files, sorted by rank.
    """
    if ranker is None:
        ranker = SuffixRanks()
    variant_map = defaultdict(set)
    for file in files:
        base = file.with_suffix("")
        variant_map[base].add(file)

    if find_variants:
        for base, variants in variant_map.items():
            variants.update(base.parent.glob(base.stem + ".*"))

    ranked_variants = {
        base: sorted(variants, key=ranker) for base, variants in variant_map.items()
    }
    return ranked_variants


@app.default
def adjust_list(
    files: list[Path],
    find_variants: bool = False,
    output: Literal["original", "generated", "rules"] = "original",
    include_single: bool = False,
):
    """
    From a list of files, print the preferred variant of a file, assuming all files with the same name but different suffixes are variants of the same resource.

    Args:
        files: List of files to consider.
        find_variants: -v, for each file foo.bar, consider all files on disk matching foo.*, not only those listed.
        output: How to print the result. "original" prints the preferred file, "generated" prints all other files, "rules" prints a makefile rule.
        include_single: Include files that have no variants.
    """
    ranked_variants = rank_variants(files, find_variants)

    for variants in ranked_variants.values():
        if len(variants) == 1 and not include_single:
            continue
        if output == "original":
            print(fspath(variants[0]))
        elif output == "generated":
            print("\n".join(map(fspath, variants[1:])))
        elif output == "rules":
            print(join(map(fspath, variants[1:])), ":", quote(fspath(variants[0])))
