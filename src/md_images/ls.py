from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from datetime import datetime
from io import StringIO
from pathlib import Path
import re
import csv
from typing import Any, Literal, cast

from humanize import naturalsize, naturaltime
from rich import box
from rich.console import Console
from rich.progress import track
from rich.table import Table

from .model import MdFile
import panflute as pf

from cyclopts import App

import logging
from . import cli  # noqa : initializes logging

logger = logging.getLogger(__name__)

app = App()


class Field(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def __call__(self, value: MdFile) -> str:
        pass

    def key(self, value: MdFile) -> Any:
        return self(value)


class TitleField(Field):
    def __call__(self, value: MdFile) -> str:
        return value.title


class NameField(Field):
    def __call__(self, value: MdFile) -> str:
        return value.path.name

    def key(self, value: MdFile) -> Any:
        parts = re.findall(r"\d+|\D+", value.path.name)
        return tuple(
            (format(int(part), "09d") if part.isdigit() else part.casefold())
            for part in parts
        )


class SizeField(Field):
    def __call__(self, value: MdFile) -> str:
        return naturalsize(value.path.stat().st_size)

    def key(self, value: MdFile) -> int:
        return value.path.stat().st_size


class ModifiedField(Field):
    def __call__(self, value: MdFile) -> str:
        return naturaltime(datetime.fromtimestamp(value.path.stat().st_mtime))

    def key(self, value: MdFile) -> float:
        return value.path.stat().st_mtime


DEFAULT_COLUMNS = [
    NameField("Name"),
    TitleField("Title"),
    SizeField("Size"),
    ModifiedField("Modified"),
]


class Ls:

    def __init__(
        self,
        what: Sequence[Path | MdFile | str] | str | None = None,
        /,
        *,
        glob: str | None = None,
        files: list[Path | MdFile | str] | None = None,
        order: Field = NameField("Name"),
        reverse: bool = False,
        columns: list[Field] = DEFAULT_COLUMNS,
    ):
        if sum(map(bool, (what, glob, files))) != 1:
            raise ValueError(
                "exactly one of `what`, `glob`, or `files` must be specified"
            )

        if what:
            if isinstance(what, str):
                glob = what
            elif what is not None and len(what) == 1:
                glob = cast(Sequence, what)[0]
            elif what is not None:
                files = list(what)
        if glob:
            files = list(Path().glob(glob))

        assert files is not None

        docs = self.load_files(files)
        self.docs = sorted(docs, key=order.key, reverse=reverse)
        self.columns = columns

    @staticmethod
    def load_files(files: Iterable[Path | MdFile | str]) -> list[MdFile]:
        result = []
        for file in track(files, "Loading files...", transient=True):
            try:
                if isinstance(file, MdFile):
                    md_file = file
                else:
                    md_file = MdFile(file)
                result.append(md_file)
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        return result

    def __rich__(self) -> Table:
        table = Table(show_header=True, box=box.SIMPLE)
        for column in self.columns:
            table.add_column(column.title)
        for doc in self.docs:
            table.add_row(*(column(doc) for column in self.columns))
        return table

    def __str__(self) -> str:
        out = StringIO()
        writer = csv.writer(out, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow([column.title for column in self.columns])
        for doc in self.docs:
            writer.writerow([column(doc) for column in self.columns])
        return out.getvalue()

    def to_pandoc(self) -> pf.Table:
        head = pf.TableHead(
            pf.TableRow(
                *[
                    pf.TableCell(pf.Plain(pf.Str(column.title)))
                    for column in self.columns
                ]
            )
        )
        body = pf.TableBody(
            *[
                pf.TableRow(
                    *[pf.TableCell(pf.Plain(pf.Str(col(doc)))) for col in self.columns]
                )
                for doc in self.docs
            ]
        )
        return pf.Table(body, head=head)


@app.default()
def ls(
    files: list[str] = ["*.md"], *, format: Literal["tsv", "pretty"] | str = "pretty"
):
    if not files:
        files = ["*.md"]
    listing = Ls(files)

    if format == "tsv":
        print(listing)
    elif format == "pretty":
        Console().print(listing)
    else:
        print(
            pf.convert_text(
                listing.to_pandoc(), input_format="panflute", output_format=format
            )
        )
