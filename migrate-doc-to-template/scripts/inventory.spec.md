# inventory.py specification

## Purpose

Produce a read-only inventory of one Word `.docx` file so an agent can plan a
template migration without guessing: what is in the document, where it is,
which parts are placeholders, and which parts must never be copied
(markings, other people's revisions, metadata).

## Interface

```text
python3 inventory.py DOCX [--json] [--full] [--width N] [--no-body]
                          [--pattern REGEX]... [--no-default-patterns]
                          [--placeholder REGEX]...
```

| Option | Behavior |
|---|---|
| `DOCX` | Path to the `.docx` to inspect. |
| `--json` | Print the full result as JSON instead of the text report. |
| `--full` | Do not truncate text in the text report. |
| `--width N` | Truncate text fields to N characters (default 160). |
| `--no-body` | Omit the body listing from the text report. |
| `--pattern REGEX` | Add a case-insensitive marking pattern. Repeatable. |
| `--no-default-patterns` | Drop the built-in marking patterns. |
| `--placeholder REGEX` | Add a placeholder pattern. Repeatable. |

`scan(path, marking_patterns=None, placeholder_patterns=None)` is the library
entry point; it returns the same dict printed by `--json`.

## Output (sections of the text report / keys of the JSON)

- `sha256` of the file (use it to prove inputs were not modified).
- `summary`: counts of paragraphs, tables, sections, images, text boxes,
  placeholders, highlighted paragraphs, tracked changes, comments, marking hits.
- `properties`: core (`creator`, `lastModifiedBy`, `title`, ...), selected
  app properties, custom properties (including sensitivity-label text), and
  `word/people.xml` authors.
- `headers_footers`: visible text per relationship-referenced header/footer
  part, regardless of the part filename.
- `sections`: page size, margins, and usable text width in inches.
- `body`: every body-level block in order.
  - `B#` is the index in `list(doc.element.body.iterchildren())`, so a build
    script can address the same element directly.
  - `T#` is the index in python-docx `doc.tables`.
  - Paragraphs show style name, numbering (`numId/ilvl`), flags
    (`IMAGE`, `TEXTBOX`, `HIGHLIGHT`, `LINEBREAKS`, `PAGEBREAK`,
    `SECTIONBREAK`), and visible text. Empty paragraphs without flags are
    omitted from the text report.
  - Tables show every row with **raw** `w:tc` cells and `span=` (gridSpan) and
    `vm=` (vMerge restart/continue) annotations. Nested tables are listed
    recursively in their containing cell. Raw cells are what a build script
    writes to.
  - `--full` disables truncation for table cells as well as other text fields.
  - Block-level content controls are flattened as `B#/sdt[i]`.
- `placeholders`: matches of the placeholder patterns with location. Defaults:
  `<...>` (excluding `<http...>`/`<mailto:...>`) and `[Add|Insert|Enter|TBD ...]`.
- `highlights`: paragraphs containing highlighted runs with text, and those runs.
- `textboxes`: text of every text box (body, headers, footers).
- `images`: relationship id, media target, size in inches, inline/anchor/vml.
- `tracked_changes`: counts per revision element, authors, and the inserted or
  deleted text with location.
- `comments`: comment count, authors and text, and body reference count.
- `markings`: hits of the marking patterns in all story parts (body, tables,
  text boxes, headers, footers, footnotes, endnotes, comments), properties,
  and `docMetadata/` parts. Defaults cover CUI, distribution statements,
  "Controlled by:", FOUO, NOFORN, classification banners (`SECRET//` etc.),
  and classification authority lines. Hits are deduplicated.

Locations: `B#` for body blocks, `B# T# r# c#` for top-level table cells
(raw cell index), `(nested table)` and `textbox` suffixes, or the part name
for headers/footers/notes.

Text-box content that Word stores twice (DrawingML plus VML fallback) is
reported once: anything inside `mc:Fallback` is skipped.

## Exit codes

- `0`: inventory produced (findings never change the exit code).
- `2`: bad input or usage: missing file, not a zip/.docx, unsafe or
  oversized package, XML parse error, or invalid regex. Message on stderr.

## Safety

- Never writes, renames, or locks the input.
- Reads the package with `zipfile` without extracting. Rejects entry names that
  are absolute, contain `..`, backslashes, or NUL. Bounds: 5000 entries,
  512 MiB uncompressed total, 64 MiB per XML part.
- Every XML part is parsed up front with entity resolution, DTD loading, and
  network access disabled. Any `<!DOCTYPE` or `<!ENTITY` declaration is
  rejected, including declarations after the first 64 KiB and UTF-16/UTF-32
  encoded declarations.
- No network access. Standard library plus `lxml` (installed with python-docx).

## Non-goals

- Not a renderer: page breaks, pagination, and visual layout are not
  computed. Check those in Word.
- Marking patterns are a safety net, not a classifier. A clean result does not
  mean a document is releasable.
- Does not read `.doc`, `.pdf`, or `.docm` macro content.

## Tests

`tests/test_inventory.py` builds synthetic documents and checks placeholder,
highlight, text-box, tracked-change, comment, footer, marking, merged-cell and
image detection, JSON output, and rejection of non-docx and DOCTYPE input.
