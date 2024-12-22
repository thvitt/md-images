## Manage Markdown Images

_md-images_ analyses markdown files (or anything else that [Pandoc](https://pandoc.org/) can read) for included images. It can report in the images, write Makefile dependencies for them, or copy the source files together with their images to a new directory.

## General Usage

```bash
md-images subcommand [options] files ...
```

See below for the available subcommands and their options.

There is also a legacy interface without subcommands, see `md-images --help`.

### Common options

* `files ...`

  The files to process. These can be markdown files or any other files that pandoc can read.

* `-s source|explicit|both`, `--select=source|explicit|both`

  Included images are often themselves generated from source files: E.g., you might include a PDF image that is converted from a source SVG by running Inkscape. md-images can find the source file for a linked image by looking at files with the same name and directory but different extensions and ranking those files according to an internal list. This option specifies which files to use:

  * `source`: Only list/copy/... the source files
  * `explicit`: Only list/copy/... the files explicitly linked in the markdown
  * `both`: Use both source and explicit files

## `md-images ls`: List image files

```bash
md-images ls [-s|--select OPTION] FILES ...
```

Lists all images included in at least one of the given source files. The output is a list of filenames, one per line. E.g., `zip docs.zip *.md $(md-images ls *.md)` creates a zip file of all markdown files in the current directory and the images they refer to.

## `md-images dep`: Write Makefile dependencies

```bash
md-images dep [-d suffix] [-i dependency_ext] FILES ...
```

Writes dependency rules for the given source files and their images. By default, the output is written to stdout and looks like this:

```makefile
foo.md : img/header.png img/logo.svg
bar.md : bottles.jpg
```

You can modify the behaviour with the following __optional arguments__:

* `-d` _suffix_, `--suffix` _suffix_  (may be given multiple times)

    Writes Makefile dependency rules using the given suffix as target.

    Suffix may be either a filename extension or a pattern containing '%'. If given multiple times, write
    multiple dependency rules.

    E.g., `md-images dep -d .pdf -d handout-%.pdf *.md` might write the following file:

    ```makefile
    foo.pdf : foo.md img/header.png img/logo.svg
    handout-foo.pdf : foo.md img/header.png img/logo.svg
    bar.pdf : bar.md bottles.jpg
    handout-bar.pdf : bar.md bottles.jpg
    ```

* `-i` _dependency_ext_, `--individual-dependencies` _dependency_ext_

    Writes one dependency file per source file that has the given extension (e.g., `.d`).

### Example

A practical Makefile making use of this command could look like this:

```makefile
MARKDOWN_FILES=$(wildcard *.md)
PDF_FILES=$(MARKDOWN_FILES:.md=.pdf)

.PHONY : default

default : $(PDF_FILES)

%.pdf : %.md
 pandoc -t latex --pdf-engine=lualatex -o $@ $<

%.pdf : %.dot
 dot -Tpdf -o$@ $<

Makefile.dep : $(MARKDOWN_FILES)
 md-images dep -d '%.pdf' $(MARKDOWN_FILES) > $@

-include Makefile.dep
```

Assuming a markdown file that includes an image:

```markdown
![Example graph](img/graph.pdf)
```

and a graphviz file `img/graph.dot`, `make` will run:

```bash
md-images dep -d '%.pdf' example.md > Makefile.dep
dot -Tpdf -oimg/graph.pdf img/graph.dot
pandoc -t latex --pdf-engine=lualatex -o example.pdf example.md
```

and thus create both the PDF file from the markdown text and the PDF image from the graphviz file `img/graph.dot`. It will cause a rebuild of both files when `img/graph.dot` is changed and of only the `example.pdf` file when `example.md` is changed.

How does this work?

The line `-include Makefile.dep` [causes make to include](https://www.gnu.org/software/make/manual/html_node/Include.html) the file Makefile.dep, but only if it exists. If it does not exist yet or if it is out of date (i.e. older than any of the markdown files), make will try to (re-)create it using the rule that calls `md-images dep` and restart. The generated, included file looks like this:

```makefile
example.pdf : example.md img/graph.pdf
```

It specifies that example.pdf is dependent on img/graph.pdf and thus triggers both the creation of img/graph.pdf and the recreation of example.pdf when img/graph.pdf or its dependency, img/graph.dot (contributed by the pattern rule for `%.pdf : %.dot`) changes.

## `md-images check`: Check whether all images are present

```bash
md-images check [-s|--select OPTION] [-v| --verbose | -q| --quiet] FILES ...
```

Checks all images included in the given text files for existence. `-s` will be respected as described above. By default, the command will exit with a return code of 1 if some image could not be found or 0 if every image exists. By default, it will also write a short report to stdout.

* `-v`, `--verbose`

    For every missing image, lists existing files with the same name but a different extension.

* `-q`, `--quiet`

    Only list the missing images, each file on a separate line.

## `md-images cp`: Copy texts with their images

```bash
md-images cp [-s|--select OPTION] FILES ... TARGET 
```

Copies the given source files and their images to the given target. Relative paths in the source files will be preserved and missing directories potentially created. Existing files will be overwritten.

* `-s`, `--select`

  See above.

* `FILES`

  The markdown (or other text) files to analyze and copy.

* `TARGET`

  If a single FILE has been given and TARGET is not an existing directory, the it is considered to be the target file name to which the FILE will be copied. In all other cases (multiple FILEs or TARGET is an existing directory) all FILES will be copied to the directory TARGET.

  All images existing in one of the given FILES will be copied to a place such that the relative path in the source file still works. Any missing directory required for any copy operation will be created.

## `md-images links`: List links

```bash
md-images links [-f|--format FORMAT] FILES ... 
```

This subcommand works on links, not images (and will probably moved to a different command in the future). It will extract all links from the given files and write them to stdout.

* `-f`, `--format` _FORMAT_

  The output format. The following formats are available:

  * `tabbed` (the default)

      A line for each link, with the three fields source file, link target, and link text, separated by tabs.
      This is the default.

  * `url`

      Only a list of URLs

  * `markdown` or any non-binary output format that pandoc can generate

      A fragment in that format, with a section for each source file and an itemized list of links for each link.
