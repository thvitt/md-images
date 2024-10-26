from functools import cached_property
from pathlib import Path

from .core import find_images, load_markdown, relative_fspath, resolve_url
from .prefer_variants import rank_variants
from typing import Callable
from shutil import copy2


class MdFile:

    def __init__(self, mdfile: str | Path) -> None:
        self.path = Path(mdfile)
        self.doc = load_markdown(self.path)

    @cached_property
    def image_urls(self) -> set[str]:
        return {img.url for img in find_images(self.doc)}

    @cached_property
    def image_paths(self) -> set[Path]:
        resolved = [resolve_url(img, self.path) for img in self.image_urls]
        return {path for path in resolved if isinstance(path, Path)}

    def image_sources(self, ranker: Callable[[Path], int] | None = None) -> set[Path]:
        ranked = rank_variants(self.image_paths, find_variants=True, ranker=ranker)
        return {variants[0] for variants in ranked.values()}

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

    def copy(self, target: Path, sources=True, generated=False) -> None:
        if target.is_dir():
            target_dir = target
            doc_target = target / self.path.name
        else:
            target_dir = target.parent
            doc_target = target
        img_sources = set()
        if sources:
            img_sources.update(self.image_sources())
        if generated:
            img_sources.update(self.image_paths)

        target_dir.mkdir(parents=True, exist_ok=True)
        copy2(self.path, doc_target)
        for img in img_sources:
            dest = target_dir / img.relative_to(self.path.parent)
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy2(img, dest)
