# migrate-doc-to-template (agent skill)

Moves the content of an older Word document (deployment guide, CAR, test
report, memo, ...) into a **copy** of a new Word template. The result keeps the
template's formatting, fonts, styles, numbering, wording, and footer. The
template and the source are never modified.

An agent follows the workflow in [SKILL.md](./SKILL.md):

1. Inventory both documents.
2. Report any markings or metadata in the source and wait for your OK.
3. Show you a slot-by-slot mapping and ask all questions at once.
4. Build the output from a copy of the template.
5. Verify the output (inputs unchanged, no markings, no tracked changes, what
   is still left to fill).
6. Give you a short report.

## Install (one time)

### Make the workflow available to your harness

Keep this folder intact: `SKILL.md`, `scripts/`, `references/`, and
`requirements.txt` must stay together. No OpenCode API or harness-specific
tool is required.

- **Harness with agent-skill support:** copy the whole folder into a skill
  directory supported by your harness. Examples include
  `.agents/skills/migrate-doc-to-template/`,
  `.github/skills/migrate-doc-to-template/`, or
  `.claude/skills/migrate-doc-to-template/` in a project, and
  `~/.config/opencode/skills/migrate-doc-to-template/` for OpenCode.
  These are alternatives, not universally supported paths. Check your
  harness's discovery rules and reload or restart if it requires that.
- **Harness without agent-skill support:** leave the folder anywhere readable
  and explicitly tell the agent to read its absolute `SKILL.md` path and
  follow the workflow. Automatic discovery and a slash command are not required.

The harness must let the agent read local files, run Python commands, create
scratch/build files, and ask the operator for approval. If any capability is
unavailable, stop and report the limitation rather than bypassing an approval
or safety check. Use only an environment approved for the documents.

### Set up Python

Install the requirements in an isolated environment. For example, on
macOS/Linux, replace `/absolute/path/to/migrate-doc-to-template` with the
folder's actual location:

```sh
cd /absolute/path/to/migrate-doc-to-template
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c "import docx; print(docx.__version__)"
```

Tell the agent to use the **absolute path** of `.venv/bin/python` for every
inventory, build, and verification command. Activation in one shell may not
persist across the harness's tool calls. On Windows, use `python -m venv .venv`
and `.venv\Scripts\python.exe` instead.

Optional self-test (synthetic files only; the tests do not use the network):

```sh
.venv/bin/python -m unittest discover -s scripts/tests -v
```

## Use

Put the files somewhere your agent can read them and ask, for example:

> Read `/absolute/path/to/migrate-doc-to-template/SKILL.md` and follow its
> workflow. Use `/absolute/path/to/migrate-doc-to-template/.venv/bin/python`.
> Move the content of `~/Documents/old/Deployment Guide v3.docx` into a copy of
> the template `~/Documents/templates/Template - Deployment Guide.docx`.
> Name the new file `Draft - Deployment Guide v4.docx` in the same folder as
> the old one.

If your harness discovers the skill automatically, you can instead ask it
to use the `migrate-doc-to-template` skill. Explicitly reading the file is
the fallback when discovery is unavailable.

Expect it to stop twice:

- **Markings check:** if the source has CUI, distribution statements,
  "Controlled by" blocks, other people's tracked changes or comments, it lists
  them and waits. These are never copied.
- **Mapping approval:** it shows which template slot gets which source
  content, what has no slot, and its questions.

After the build, open the output in Word and check the layout (page breaks,
table splits, picture size). The tool cannot render pages.

## Rules it follows (short version)

- The template wins on format and wording. Source data goes only into template
  slots.
- Anything the template has no slot for is dropped and listed. Nothing is added
  "to be helpful".
- Slots with no source data keep the template placeholder and are listed.
- Source text is copied verbatim. Inconsistencies are flagged, not fixed.
- It never overwrites a file, never edits the template or source, and never
  commits or uploads.

## Scripts (usable on their own)

| Script | What it does |
|---|---|
| `scripts/inventory.py FILE.docx` | Read-only listing of everything in a .docx: body, tables (with merges), placeholders, highlights, text boxes, images, headers/footers, properties, tracked changes, comments, and marking hits. `--json` for machine output. |
| `scripts/verify.py --output OUT.docx --unchanged TEMPLATE SHA256 ...` | Post-build checks. Exit code 0 = pass, 1 = fail, 2 = usage/input error. |
| `scripts/docx_helpers.py` | Library used by the per-job build script (copy without overwrite, multi-run replace, fill cells, clone rows, pictures, ...). |

Each script has a `*.spec.md` with its exact behavior, and there are tests in
`scripts/tests/`.

## Data handling

Follow your organization's rules on which documents may be processed with AI
tools. The skill keeps markings out of the output, but it does not decide
whether a document may be opened in the first place. Built-in marking
patterns are a safety net, not a classifier.

## Requirements

- An agent harness with the local file, Python execution, and operator
  approval capabilities listed above
- Python 3.8+ with `python-docx` 1.1 or later (pulls in `lxml`)
- Microsoft Word for the final visual check
