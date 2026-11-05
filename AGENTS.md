# Agent instructions

## Start here

- Read the root `README.md` and the relevant script documentation before
  changing repository content.
- For changes to `scripts/`, read that script's `*.spec.md`, its tests, and
  `scripts/README.md` before editing. Treat the specification as the behavior
  contract.
- Read and follow any applicable `.github/instructions/*.instructions.md`
  files before writing or modifying code.
- Inspect `git status --short` before work. This repository may contain
  operator-authored data, local source bundles, ignored product trees, or
  other in-progress changes. Never discard changes that are not yours.

## Repository model

- `VPN/<rule-id>/srg.txt` is shared baseline content.
- `VPN/<product>/<rule-id>/*.txt` contains product-specific material.
- `configs/` contains example device configuration files. Values in examples
  should remain placeholders; never add real pre-shared keys, passwords,
  tokens, or private keys.
- `scripts/stig-view.sh` is a read-only viewer.
- `scripts/x2stighub.py` imports XML or Excel into the repository layout.
- `scripts/extract_srg.py` extracts the approved SRG archive.
- `srgs/` and `zips/` are local source-data locations and may be absent from a
  clean clone.

Do not conflate source requirements with product implementation guidance.
Do not rewrite user-authored nonblank content as a side effect of an import.
The importer is designed to fill only missing or whitespace-only files; it
does not refresh populated files when source content changes.

## Data safety and Git

- Review every planned content-generation command and its output root before
  running it. Prefer temporary output for tests and experiments.
- Do not use existing production or operator-authored product directories as
  scratch output.
- The root `.gitignore` currently ignores `zips/`, `srgs/`, and
  `/VPN/Cisco-*/`, as well as Python caches and virtual environments. Check
  `git status --short --ignored` and `git check-ignore -v <path>` when data
  appears missing from ordinary Git status.
- Do not force-add ignored source data or generated trees, or change ignore
  policy, without an explicit task requirement.
- Preserve tracked files and directory layout unless the task specifically
  requests a migration. Report unexpected deletions or conflicts rather than
  resolving them by reverting files.

## Script behavior and validation

- Keep the scripts local-only; do not introduce network access or device
  changes unless explicitly requested.
- Keep input validation, path safety, preservation semantics, and failure
  reporting covered by the existing script contracts and tests.
- For XML handling, preserve the current DTD rejection and parser limits.
- For archive handling, preserve path/type checks, resource bounds, staging,
  and no-overwrite behavior.
- For file handling, do not follow output symlinks or silently replace
  authored content.
- Do not add credentials or real secrets to examples, tests, documentation,
  or generated fixtures.

## Tests

From the repository root, run the focused test module for a narrowly scoped
script change, then run the full suite when the change affects shared
behavior:

```sh
uv run --no-project --with-requirements scripts/requirements.txt \
  python -m unittest discover -s scripts/tests -v
bash -n scripts/stig-view.sh
```

The importer supports standard-library XML imports without `openpyxl`, but
the complete workbook tests and Excel operations require the dependency in
`scripts/requirements.txt`. Keep tests isolated from repository data and do
not regenerate the live VPN content just to validate unrelated code.

## Documentation

Keep operator instructions accurate to the current command-line help and
specifications. Clearly distinguish local/ignored source assets from files
tracked by Git, and call out commands that create or fill content. Do not
claim that data is current, compliant, validated against an XSD, or
device-tested unless that evidence exists.
