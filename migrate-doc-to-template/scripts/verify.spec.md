# verify.py specification

## Purpose

Check a migrated `.docx` before it is handed to the operator. Confirm the
inputs were not modified, the output opens, and the output carries no tracked
changes, comments, markings, or forbidden text. List anything still left to
fill.

## Interface

```text
python3 verify.py --output OUT.docx
                  [--unchanged PATH SHA256]...
                  [--forbid REGEX]... [--no-default-patterns]
                  [--placeholder REGEX]...
                  [--strict] [--allow-revisions] [--allow-comments] [--json]
```

| Option | Behavior |
|---|---|
| `--output` | The migrated document. Required. Never modified. |
| `--unchanged PATH SHA256` | An input (template, source) that must still hash to `SHA256`. Repeatable. Using the output path here is a usage error. |
| `--forbid REGEX` | Case-insensitive text that must not appear anywhere in the output (for example the source document's organization or tester name). Added to the default marking patterns. Repeatable. |
| `--no-default-patterns` | Check only the `--forbid` patterns. |
| `--placeholder REGEX` | Extra placeholder pattern, added to inventory's defaults. |
| `--strict` | Remaining placeholders and highlighted text fail instead of warn. |
| `--allow-revisions` | Tracked changes warn instead of fail. |
| `--allow-comments` | Comments warn instead of fail. |
| `--json` | Print `{"result": ..., "checks": [...]}`. |

`verify(...)` is the library entry point and returns
`(status, checks, scan_result)`.

## Checks

| Check | Result |
|---|---|
| input unchanged | FAIL if a `--unchanged` file is missing or its SHA-256 differs. WARN if the output is byte-identical to an input. |
| output opens | FAIL if the package is invalid or unsafe (see inventory.spec.md), or python-docx cannot load it. WARN if python-docx is not installed. |
| no tracked changes | FAIL on any revision element (`w:ins`, `w:del`, `w:moveFrom/To`, `*PrChange`), listing authors and text. |
| no comments | FAIL on any comment or comment reference. |
| no markings/forbidden text | FAIL on any marking or `--forbid` hit in any story part, property, or `docMetadata/` part. |
| placeholders remaining | WARN (FAIL with `--strict`), listing each with location. |
| highlighted text remaining | WARN (FAIL with `--strict`), listing each with location. |
| file properties, headers/footers, output sha256 | INFO only. |

Template boilerplate can legitimately match a `--forbid` pattern. Review each
hit and report it to the operator. Do not edit template wording to make the
check pass.

## Exit codes

- `0`: no FAIL checks (warnings allowed).
- `1`: at least one FAIL check.
- `2`: usage or input error: output missing, malformed SHA-256, invalid
  regex, `--unchanged` naming the output, or unreadable/unsafe package.

## Safety

- Read-only for every path it is given.
- Uses inventory.py's bounded, DTD-free package reader. No network access.

## Tests

`tests/test_verify.py` covers a passing output, a changed input, tracked
changes, comments, default marking hits, `--forbid`, `--strict`, the allow
flags, identical output, malformed SHA-256, and the output passed as an
`--unchanged` input.
