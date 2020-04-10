## Extract Markdown Images

This script can be used to find out which images are externally linked from one or more given Markdown files, or, 
in fact, other files that [Pandoc](https://pandoc.org/) can read. It has been written for two use cases:

* copying a markdown file and all its dependencies to a different folder
* generating Makefile representing the inclusions as dependencies.


## Usage

```
md-images [-h] [-d suffix] [-i suffix] [-l] [-f FORMAT] [-k] markdown [markdown ...]
```

* `markdown`: Markdown files to read. This can also be other files that pandoc can read, e.g., html or jupyter notebooks.

Without any options, md-images writes a list of dependencies for each given file:

```
foo.md : img/header.png img/logo.svg
bar.md : bottles.jpg
```

You can modify the behaviour with the following __optional arguments__:

*  `-d` _suffix_, `--suffix` _suffix_  (may be given multiple times)

    Writes Makefile dependency rules for the given default
    suffix. Suffix may be either a filename extension or a
    pattern containing '%'. If given multiple times, write
    multiple dependency rules.
    
    E.g., `md-images -d .pdf -d handout-%.pdf *.md` might write the following file:
    
    ```makefile
    foo.pdf : foo.md img/header.png img/logo.svg
    handout-foo.pdf : foo.md img/header.png img/logo.svg
    bar.pdf : bar.md bottles.jpg
    handout-bar.pdf : bar.md bottles.jpg
    ```
   
* `-i` _suffix_, `--individual-dependencies` _suffix_

    Together with one or more `-d` options, writes one dependency file per source file,
    with the given suffix.
    
* `-l`, `--list` 

    Only list the dependent images. E.g., `zip docs.zip *.md $(md-images -l *.md)` creates 
    a zip file of all markdown files in the current directory and the images they refer to.
     
     
*  `-f` _format_, `--format` _format_

    Enforced format of the source files. If this is not given, the tool will try to guess
    from the filename extension and when that is not known, fall back to Markdown.
    
*  `-k`, `--keep-going`
      
    Do not quit on errors. Errors are most likely parse errors of the source file. With
    `-k`, a short error message will be written to stderr and a comment will be added to
    the output. Without `-k`, 
    
    
*  `-h`, `--help`

    show a help message and exits.


## Examples

The following Makefile:

```makefile
MARKDOWN_FILES=$(wildcard *.md)
PDF_FILES=$(MARKDOWN_FILES:.md=.pdf)

.PHONY : default

default : $(PDF_FILES)

%.pdf : %.md
    pandoc -t latex --pdf-engine=lualatex -o $@ $<

Makefile.dep : $(MARKDOWN_FILES)
    md-images -d '%.pdf' $(MARKDOWN_FILES)

-include Makefile.dep
```

will use Pandoc and luaLaTeX to build a PDF file out of every markdown file in the current directory. Whenever one of the images linked from a markdown file is modified, the corresponding PDF will be rebuilt.

You can also use this to compile the _images_, if they need to. Assume you have a graph that you’re authoring in Graphviz’ `.dot` format in `img/graph.dot` and the following additional rule in your makefile:

```makefile
%.pdf : %.dot
	dot -Tpdf -o$@ $<
```

Now, when you include a reference to the corresponding PDF file in your markdown:

```markdown
![Example graph](img/graph.pdf)
```

md-images will detect the dependency and write it to the include file, make will detect the missing dependency `img/graph.pdf` and make it using the implicit rule from the existing `.dot` file.