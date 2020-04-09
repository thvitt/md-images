## Markdown Images

Scan a markdown file for included images (using pandoc/panflute). May output simple lists (useful for copying) or Makefile snippets. The latter can be useful for automatic dependency generation, e.g., if you have a makefile that has its markdown files in a variable, this snippet:

```make
Makefile.dep : $(MARKDOWN_FILES)
    md-images -d '%.pdf' $(MARKDOWN_FILES)

include Makefile.dep
```

will automatically create rules like

```make
foo.pdf : foo.md img/pic1.png img/pic2.pdf
```

