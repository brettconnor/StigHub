# docx_helpers.py specification

## Purpose

A small library for per-job build scripts that fill a **copy** of a Word
template with content from a source document. It keeps the template's
formatting by writing into the template's own runs, cells, and paragraphs. It
never writes the template file.

## Usage

```python
import sys
sys.path.insert(0, "<skill_dir>/scripts")
from docx_helpers import *

digest = copy_template(TEMPLATE, OUTPUT)      # never overwrites
src, out = open_docx(SOURCE), open_docx(OUTPUT)
p = find_one(out, r"SYSTEM TITLE")
replace_span(p, "<Add System Name>", "Example System")
strip_highlight_if_filled(p)
out.save(OUTPUT)
assert_unchanged(TEMPLATE, digest)
```

## Contract

### Files

| Function | Behavior |
|---|---|
| `copy_template(template, output)` | Copies byte-for-byte with exclusive create (`open(..., 'xb')`). Raises `FileNotFoundError` (template or output folder missing), `FileExistsError` (output path exists, including a dangling symlink), `ValueError` (same path), `RuntimeError` (template changed during copy or copy differs). Returns the template SHA-256. |
| `assert_unchanged(path, digest)` | `RuntimeError` if the file's SHA-256 differs. |
| `sha256_file(path)` | Hex digest. |
| `open_docx(path)` | `docx.Document(path)`. |

### Navigation (indices match inventory.py)

| Function | Behavior |
|---|---|
| `body_blocks(doc)` | `list(doc.element.body.iterchildren())`; index = inventory `B#`. |
| `tables(doc)` | Top-level `w:tbl` elements; index = inventory `T#` = `doc.tables` index. |
| `rows(tbl)`, `cells(tr)` | Raw `w:tr` / `w:tc` children. `cells` are physical cells: a `gridSpan` cell appears once; `vMerge` continuation cells are separate elements. |
| `read_table(table)` | Merge-resolved text grid from a python-docx `Table` (one entry per grid column, merged text repeated). For reading the source. |
| `text_of(el)` | All `w:t` text below `el`, including text boxes. |
| `para_text(p)` | Visible paragraph text (tabs `\t`, breaks `\n`), excluding text boxes anchored in it. Accepts `w:p` or python-docx `Paragraph`. |
| `cell_lines(tc)` | Stripped non-blank paragraph texts of a cell. |
| `find_paragraphs(root, pattern, flags=0, include_tables=True, include_textboxes=False)` | Paragraphs whose visible text matches `re.search`. `root` is a `Document` or element. Skips `mc:Fallback` duplicates. |
| `find_one(root, pattern, **kw)` | Exactly one match, else `LookupError` listing the matches. |
| `expect(el, fragment)` | `AssertionError` unless `fragment` is in the element's text. Use it to guard index-based addressing. |

### Writing text (template formatting kept)

| Function | Behavior |
|---|---|
| `replace_span(p, old, new)` | Replaces the first `old` in visible paragraph text even when it spans several runs. Tabs and line breaks participate in matching, so a match cannot cross them unless `old` includes them. New tabs and line breaks become Word tab/break elements. `new` goes into the run holding most of `old`, keeping that run's formatting. Highlight is removed from every affected run. `LookupError` if not found. |
| `set_paragraph_text(p, text)` | Replaces all visible text. Keeps the first text run's formatting and the `pPr` (style, numbering, indentation). Removes text, tab and break content from other runs, including runs containing only tabs or breaks (drawings and fields stay). New tabs and line breaks become Word tab/break elements. Strips highlight. |
| `fill_cell(tc, lines, proto_tc=None, **fmt)` | Replaces the cell's paragraphs with one per line. `pPr` and `rPr` come from the first text-bearing paragraph of `proto_tc` (default: the cell). Highlight is stripped. `tcPr` (width, borders, merges) is untouched. `''` gives an empty paragraph. |
| `new_run(rpr_proto, text, bold=, italic=, underline=, color=)` | New run with a copy of `rpr_proto`, minus highlight and revision marks. `\n` becomes `w:br` and `\t` becomes `w:tab`. Overrides apply only when not `None`. `rPr` children are inserted in ECMA-376 order. |
| `append_run(p, text, rpr_proto=None, **fmt)` | Appends `new_run(...)` to `p`. |
| `remove_runs(p, start=0, end=None)` | Removes direct-child runs in the slice. |
| `set_rpr(rpr, tag, attrs)` | Sets (dict) or removes (`None`) one `rPr` child in schema order. |
| `strip_highlight(el)` | Removes every `w:highlight` at or below `el`. |
| `strip_highlight_if_filled(el, pattern=PLACEHOLDER_RE)` | For each paragraph with no placeholder left, removes all highlight. This catches neighbouring runs that were highlighted as part of a placeholder. Returns whether anything changed. |

### Structure

| Function | Behavior |
|---|---|
| `clone(el)` | Deep copy. |
| `clone_after(el, n=1)` | Inserts `n` deep copies after `el`; returns them in order. Use it for extra table rows or list items. |
| `insert_after(ref, els)` | Inserts `els` after `ref` in order; returns the last one. |
| `remove(el)` | Detaches `el`. |
| `is_blank(el)` | No visible text and no drawing, picture, or text box. |
| `remove_blank_rows(tbl, first=1)` | Removes fully blank rows from index `first` on; returns the count. Not for intentionally blank rows (revision history, sign-off). |

### Carrying emphasis from the source

| Function | Behavior |
|---|---|
| `run_specs(p)` | Source paragraph to `[(text, {bold, italic, underline, color})]`. Keeps emphasis only, not fonts, sizes, or highlight. Black/auto color is reported as `None`. Adjacent runs with equal emphasis are merged. |
| `paragraph_from_specs(ppr_proto, specs, rpr_proto=None)` | New `w:p` from a copy of a template `pPr` (highlight stripped), with one run per spec on top of `rpr_proto`. |

### Images

| Function | Behavior |
|---|---|
| `list_images(doc)` | Body images in order: block index, rId, part name, content type, size in inches. |
| `extract_image(doc, rid, out_path)` | Writes the image blob. Never overwrites (`FileExistsError`). |
| `text_width_inches(doc, section_index=0)` | Page width minus left and right margins. |
| `put_picture(doc, p, image_path, width_in, section_index=0)` | Replaces the runs of `p` with an inline picture (aspect kept). `ValueError` if wider than the text width. Body and table paragraphs only. |

## Safety

- Never writes the template or source. Output is created with exclusive create.
- No network access. Requires `python-docx` (which brings `lxml`).
- Only edits the document object in memory. The caller saves it.

## Non-goals

- No layout or pagination. Visual checks happen in Word.
- No automatic mapping. The agent decides each slot with the operator.
- No header or footer picture insertion; headers and footers keep the template's.

## Tests

`tests/test_docx_helpers.py` covers the copy/no-overwrite rules, multi-run
replacement with formatting kept and highlight removed, `fill_cell` with
prototypes, row cloning, `find_one` errors, `strip_highlight_if_filled`,
`set_rpr` ordering, `run_specs`/`paragraph_from_specs`, `read_table` merge
resolution, and picture insertion and size limits.
