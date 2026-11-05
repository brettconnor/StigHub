---
name: migrate-doc-to-template
description: Migrates the content of an older Word document (.docx) - deployment guide, assessment report (CAR), test report, procedure, memo - into a copy of a new Word template, keeping the template's formatting, fonts, styles, numbering, and wording. Use when the user asks to move, port, convert, or copy an old document's data into a new template or new format.
---

# Migrate a document into a new template

Fill a **copy** of a Word template with the data from an older source
document. The template decides how the result looks and reads. The source
only supplies data.

The scripts live in `scripts/`, next to this file. Use the absolute path of
this skill's base directory when running them (shown as `<skill>` below).

## Harness compatibility

This workflow does not require a particular agent harness. Load it through
the harness's skill mechanism, or read this file explicitly if skills are not
supported. Resolve `<skill>` from this file's location, not the working directory.

Use the harness's available file-reading, file-editing, command-execution, and
operator-question tools. Ask approval questions in a structured form when
available, otherwise in chat; in either case wait for the operator's answer.
If required tools, local file access, or an interactive approval channel are
unavailable, stop and report the limitation. Do not skip the approval gates.
Follow the harness's permissions and the organization's document-handling policy.

Use the operator's configured Python interpreter for **every** command,
including the per-job build script. The examples below use `python3`; replace
it with the configured interpreter's absolute path when using a virtual
environment. Do not rely on shell activation persisting between tool calls.

## Hard rules

1. **Never modify the source or the template.** Work only on a new copy of the
   template. Record both inputs' SHA-256 before building and verify them after.
2. **Never overwrite an existing file.** Ask the operator for the output name
   and folder. Propose a name that follows the template's file-naming pattern.
3. **The template is authoritative** for structure, section order, wording,
   boilerplate, styles, fonts, numbering, headers/footers, footer/sensitivity
   marking, and attribution (organization, tester, author names in text).
4. **Source data goes only into template slots.** A slot is:
   - placeholder text (`<...>`, `[Add ...]`, highlighted text);
   - empty data rows in tables;
   - sample entries that are obviously examples, such as a list of section
     headings for a different product.

   If you are unsure whether template text is a slot or boilerplate, ask.
5. **If it is not in the template, it does not go in.** Do not add sections,
   tables, notes, acronyms, defaults, or "helpful" extras, even when the source
   has them. Content without a slot is dropped and listed in the report,
   unless the operator explicitly approves adding it.
6. **Never paste source formatting.** Write text into the template's own runs
   and cells. For more rows, paragraphs, or list items, clone the template's
   own element. Remove unused blank data rows, but keep intentionally blank
   rows (revision history, sign-off) unless told otherwise.
7. **Slots with no source data keep the template's placeholder** and are
   listed in the report. Never invent values.
8. **Never carry over markings or metadata from the source.** This covers
   CUI/classification banners, distribution statements, "Controlled by"/POC
   blocks, other people's tracked changes and comments, and author names. Report
   them. Do not decide handling policy yourself. The output keeps the template's
   footer/marking unless the operator says otherwise.
9. **Copy source text verbatim.** Do not fix, reword, or summarize it. The only
   exceptions are grammar needed to fit a template sentence and wording the
   operator approves. List every wording change in the report.
10. **Flag inconsistencies, do not fix them.** Examples: mismatched counts, part
    numbers, names, or dates in the source, and leftover template filler in the
    source (for example a stray highlighted "Component Name"). Skip the filler.
11. **Restructuring needs approval.** For example, turning a prose list into a
    template table. Keep every item and verify counts and totals in the build
    script.
12. **Revision history:** a migrated document is normally a new document, so
    ask. The usual answer is one initial entry dated today, not the source's
    history.
13. **Ask in batches.** Collect all open questions and ask them together. When
    you suggest an answer, it must come from the template or the source, never
    from your own assumptions.
14. Never commit, upload, email, or share the output. That is the operator's
    decision.

If a source is `.doc`, `.pdf`, or `.docm`, ask the operator to save it as
`.docx` in Word first.

## Workflow

### Step 0: Intake

- Confirm paths: source document(s), template, output folder, and output file
  name. If the operator gave a template from a "do not modify" area, that is
  fine: it is only read.
- Check the configured interpreter: `python3 -c "import docx"` (substitute
  the interpreter path as described above). If that fails, stop and point
  the operator to [README.md](./README.md) for setup. Do not install packages
  without asking.
- Create a scratch folder outside the operator's document folders, for
  example a unique job directory under the operating system's temporary
  directory. Build scripts, extracted images, and inventories go there.

### Step 1: Inventory both documents

```sh
python3 <skill>/scripts/inventory.py "<template.docx>" --full > <scratch>/template.inv.txt
python3 <skill>/scripts/inventory.py "<source.docx>"   --full > <scratch>/source.inv.txt
```

Read both inventories completely. `B#` labels are body-child indices and `T#`
labels are `doc.tables` indices; both match `docx_helpers.body_blocks()` /
`tables()`. Table cells are **raw** cells with `span=`/`vm=` annotations.
Note:

- every template slot (placeholders, highlighted text, sample rows/headings);
- template boilerplate that refers to things (table numbers, paragraph numbers,
  RAE lists, tool versions) that may not match the source;
- source sections, tables (including merges), images, and text boxes.

### Step 2: Markings and metadata (STOP if anything is found)

Review these sections of the source inventory: MARKINGS, TEXT BOXES,
TRACKED CHANGES, COMMENTS, HEADERS / FOOTERS, PROPERTIES. Marking patterns
are a safety net, so also read the text boxes and headers yourself.

- Report each finding with its location.
- If anything resembling a marking, distribution statement, or controlled
  content is present, **stop and wait for the operator's explicit go-ahead.**
- These items are never copied into the output, whatever the answer.

### Step 3: Mapping (STOP for approval)

Fill in `references/mapping-worksheet.md` (copy it to the scratch folder).
Present to the operator:

1. Template slot to source content for every slot, including the number of
   rows or paragraphs to clone.
2. Template slots with no source data (they stay as placeholders).
3. Source content with no template slot (dropped unless approved).
4. Source inconsistencies and leftover filler found.
5. All open questions, in one batch.

Do not build until the operator approves the mapping.

### Step 4: Build

Write `<scratch>/build.py` using the helpers. Requirements:

- Call `copy_template()` first and keep the returned digest.
- Locate every slot by text (`find_one`) or by inventory index guarded with
  `expect()`, so the script fails loudly if the template is not as expected.
- Read source values from the source document in code (`read_table`,
  `cell_lines`, `para_text`, `run_specs`) instead of retyping them. Assert
  expected counts (rows, items, totals).
- After filling a paragraph or cell, call `strip_highlight_if_filled()` so
  highlighted neighbour runs of the placeholder are cleared too.
- Save, then `assert_unchanged(template, digest)`.

If the build fails partway, delete only the output file this job created, fix
the script, and rerun. `copy_template` refuses to overwrite. Never hand-edit
the output XML.

```python
import sys
sys.path.insert(0, "<skill>/scripts")
from docx_helpers import *

TEMPLATE, SOURCE, OUTPUT = "...", "...", "..."
digest = copy_template(TEMPLATE, OUTPUT)
src_digest = sha256_file(SOURCE)
src, out = open_docx(SOURCE), open_docx(OUTPUT)

# -- read source
name = para_text(find_one(src, r"^System Name:")).split(":", 1)[1].strip()
src_rows = read_table(src.tables[2])[1:]          # merge-resolved, skip header

# -- simple placeholder
p = find_one(out, r"SYSTEM TITLE")
replace_span(p, "<Add System Name>", name)
strip_highlight_if_filled(p)

# -- table: clone the template's own data row as needed
tbl = tables(out)[1]
first = rows(tbl)[1]
expect(first, "<Add Component>")
proto = [clone(c) for c in cells(first)]
targets = [first] + clone_after(first, len(src_rows) - 1)
for tr, data in zip(targets, src_rows):
    for tc, pc, value in zip(cells(tr), proto, data):
        fill_cell(tc, value.split("\n"), proto_tc=pc)
remove_blank_rows(tbl)

# -- repeated block (heading + body paragraphs): clone the template's block
# -- picture: put_picture(out, find_one(out, "<Add System Diagram>"), img, text_width_inches(out) - 0.5)

out.save(OUTPUT)
assert_unchanged(TEMPLATE, digest)
assert_unchanged(SOURCE, src_digest)
print("template sha256", digest, "source sha256", src_digest)
```

See `scripts/docx_helpers.spec.md` for every helper.

### Step 5: Verify

```sh
python3 <skill>/scripts/verify.py --output "<output.docx>" \
  --unchanged "<template.docx>" <template_sha256> \
  --unchanged "<source.docx>" <source_sha256> \
  [--forbid "<source-only org or tester name>"]...
```

- FAIL results must be fixed in `build.py` and the output rebuilt.
- `--forbid` hits inside template boilerplate are not errors to "fix": report
  them to the operator.
- Re-run `inventory.py` on the output. Confirm every mapped slot is filled and
  every remaining placeholder is on the "no source data" list.
- LibreOffice/Word rendering is not available to you. The operator checks the
  layout in Word.

### Step 6: Clean up

Delete extracted images and other temporary files in the scratch folder.
Keep `build.py` only if the operator wants it, and tell them where it is.
Never delete anything outside the scratch folder except a failed output this
job created.

### Step 7: Report

Keep it short and use this order:

1. Output path, and confirmation that the template and source are unchanged
   (SHA-256 verified).
2. What was filled (by section/table), including rows or paragraphs added by
   cloning.
3. Placeholders still open, with locations.
4. Source content dropped (no template slot).
5. Markings and metadata found in the source and not copied.
6. Source inconsistencies and leftover filler.
7. Assumptions and wording changes made (with operator approval).
8. Template boilerplate that may not fit the new content (left unchanged).
9. File properties inherited from the template (author, last modified by).
   Mention that Word's File > Info > Inspect Document can clear them.
10. "Check the layout in Word": page breaks, table splits, image size.

## Word / python-docx pitfalls

- `doc.paragraphs` skips tables, text boxes, headers, and footers. Use the
  inventory to see everything.
- Text boxes can hold markings and tracked changes. Word often stores each
  text box twice (DrawingML plus `mc:Fallback` VML). The helpers skip fallbacks.
- **Merged cells:** python-docx `row.cells` is merge-resolved (good for
  *reading*). Raw `cells(tr)` are physical cells (use these for *writing*).
  Write only to the `vm=restart` cell of a vertical merge and leave
  continuation cells empty.
- Placeholders are often split across several runs, and the neighbouring runs
  (" Software Release ") can be highlighted too. Use `replace_span` and then
  `strip_highlight_if_filled`.
- The paragraph mark (`pPr/rPr`) can carry highlight that colours text added
  later. The helpers strip it.
- Auto-numbered paragraphs (inventory `num=`) renumber themselves when
  cloned. Hard-coded numbers like "(6)" must be changed in text.
- Some templates use manual line breaks and leading spaces inside a paragraph.
  Filling them leaves ragged lines. Leave the template text alone and report it.
- Cross-references in boilerplate ("Table 2", "Paragraph 9") may no longer
  match. Report them; do not edit.
- Size pictures to the template's text width (`text_width_inches`). Drop the
  source's legends and captions unless the template has a slot for them.
- python-docx `Section` widths subtract to plain ints, not `Length`. Divide by
  914400 for inches (or use `text_width_inches`).
- Keep `rPr` children in schema order (`set_rpr` does). Word refuses files with
  misordered elements.

## Do not

- Do not run any tool that writes to the template or source, including
  "Save" in python-docx on an input path.
- Do not add content to make the document "complete".
- Do not drop template boilerplate because it seems irrelevant. Report it.
- Do not copy the source's footer/header, sensitivity label, or file properties.
