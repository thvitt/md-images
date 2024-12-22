from enum import Enum
from functools import cached_property
from pathlib import Path

from panflute import stringify

from .core import find_images, load_markdown, relative_fspath, resolve_url
from .prefer_variants import rank_variants
from typing import Callable
from shutil import copy2
import logging

logger = logging.getLogger(__name__)


class SourceSelection(Enum):
    """
    If *explicit*, only include image files listed in the text file.
    If *source*, look for a file with preferred extensions but the same
    name and directory as the listed file and include that instead,
    if it exists. If *both*, include both.
    """

    EXPLICIT = "explicit"
    SOURCE = "source"
    BOTH = "both"
    ALL = "all"


class MdFile:

    def __init__(self, mdfile: str | Path) -> None:
        self.path = Path(mdfile)
        self.doc = load_markdown(self.path)

    def __str__(self) -> str:
        result = str(self.path)
        try:
            title = stringify(self.doc.metadata["title"])
            result += f" ({title})"
        except Exception:
            pass
        return result

    @cached_property
    def image_urls(self) -> set[str]:
        return {img.url for img in find_images(self.doc)}

    @cached_property
    def image_paths(self) -> set[Path]:
        resolved = [resolve_url(img, self.path) for img in self.image_urls]
        return {path for path in resolved if isinstance(path, Path)}

    def image_sources(
        self,
        selection: SourceSelection = SourceSelection.SOURCE,
        ranker: Callable[[Path], int] | None = None,
    ) -> set[Path]:
        result = set()
        if selection == SourceSelection.EXPLICIT or selection == SourceSelection.BOTH:
            result |= self.image_paths
        if selection != SourceSelection.EXPLICIT:
            ranked = rank_variants(self.image_paths, find_variants=True, ranker=ranker)
            if selection == SourceSelection.SOURCE or selection == SourceSelection.BOTH:
                result |= {variants[0] for variants in ranked.values()}
            elif selection == SourceSelection.ALL:
                for variants in ranked.values():
                    result.update(variants)
        return result

    def rule(self, suffix: str | None = None, base: Path = Path()) -> str:
        if suffix is None:
            target = self.path
            deps = []
        else:
            if "%" in suffix:
                target = self.path.with_name(suffix.replace("%", self.path.stem))
            else:
                target = self.path.with_suffix(suffix)
            deps = [self.path]
        deps.extend(self.image_paths)

        return f"{relative_fspath(target, base)} : {' '.join(relative_fspath(dep, base) for dep in deps)}"

    def copy(self, target: Path, selection: SourceSelection = SourceSelection.SOURCE):
        if target.is_dir():
            target_dir = target
            doc_target = target / self.path.name
        else:
            target_dir = target.parent
            doc_target = target

        target_dir.mkdir(parents=True, exist_ok=True)
        copy2(self.path, doc_target)
        images = self.image_sources(selection)
        logger.info(
            "Copied text file %s to %s, %d images will follow",
            self.path,
            doc_target,
            len(images),
        )
        for img in images:
            dest = target_dir / img.relative_to(self.path.parent)
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy2(img, dest)
            logger.debug("   %s: copied image file %s to %s", self.path, img, dest)
