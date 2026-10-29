# Add bleed to an illustrated PDF without reflow

The general PDF-preserve profile can explicitly extend source edge colours into
new exterior bleed. Text, vectors, illustrations and their relative positions
inside the original trim remain at 100% scale. No Markdown conversion is used.

```sh
python scripts/build_book.py --input source.pdf --output-dir output-new \
  --profile general --mode preserve --trim 6x9 --bleed \
  --bleed-strategy extend_edges --print-cleanup
```

The default strategy remains `validate`: enabling `--bleed` alone reports missing
bleed without altering page geometry. The new strategy rejects rotated pages or
pages whose size/origin does not match the selected trim, including sources that
already have bleed. It refuses existing output paths as the normal builder does.

For a 6x9-inch source, output pages are 6.125x9.25 inches. The first selected page
is recto; subsequent pages alternate outside bleed on right/left. Top and bottom
bleed are 0.125 inch each. MediaBox/BleedBox include bleed and TrimBox identifies
the unchanged original content. Single-pixel edge samples extend only beyond
the trim. These strips are excluded from the artwork-resolution warning count.

`--print-cleanup` removes link annotations and unembedded font resources proven
not to show text, including nested/shared Form resources. Used fonts remain.
Other annotation types require a separately flattened print source so visible
annotation appearances are not silently discarded.

Dependencies are pypdf, Pillow, ReportLab and Poppler's `pdftoppm`. No AI calls,
account credentials or paid services are involved. The DirectorHelp renderer and
default preservation route remain unchanged.

Edge continuation is reconstructed from the supplied border pixels. It cannot
recover missing image detail, fix source editorial issues or certify acceptance.
Compare the trimmed output to the source and review KDP Previewer plus a physical
proof before publication. Confirm ink, paper, page count and cover dimensions
for the actual title separately.
