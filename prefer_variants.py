from posix import fspath
from collections import defaultdict
from pathlib import Path
from typing import Literal
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
    variant_map = defaultdict(set)
    for file in files:
        base = file.with_suffix("")
        variant_map[base].add(file)

    if find_variants:
        for base, variants in variant_map.items():
            variants.add(base.parent.glob(base.stem + ".*"))

    ranker = SuffixRanks()
    ranked_variants = {
        base: sorted(variants, key=ranker) for base, variants in variant_map.items()
    }

    for variants in ranked_variants.values():
        if len(variants) == 1 and not include_single:
            continue
        if output == "original":
            print(fspath(variants[0]))
        elif output == "generated":
            print("\n".join(map(fspath, variants[1:])))
        elif output == "rules":
            print(join(map(fspath, variants[1:])), ":", quote(fspath(variants[0])))
