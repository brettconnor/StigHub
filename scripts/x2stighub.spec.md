# x2stighub importer specification

Status: implementation contract, 2026-11-04.

## Scope and interface

S1. Import `.xml` XCCDF Benchmarks (namespaces 1.1 and 1.2) and `.xlsx`
workbooks. Reject other extensions, including ZIP, with a useful error.
With no arguments retain the original prompt order: SRG shortname, input,
Excel start/end rows when applicable, OS/product name. Also support
`--input`, `--srg`, `--product`, `--output-root` (default current directory),
and Excel-only `--start-row`/`--end-row`. Partial command-line configurations
must fail rather than unexpectedly prompt. Success exits 0; invalid input
or filesystem failures exit nonzero with a concise error and no traceback.
For a shared baseline without product templates, accept `--baseline-only`
instead of `--product`; require `--input` and `--srg` and reject combining
`--baseline-only` with `--product`. No-argument interactive prompts are unchanged.

S2. Under `<output-root>/<srg>`, write shared `<rule>/srg.txt` and
`<product>/<rule>/{requirement,vuldiscussion,status,check,severity,fix,
mitigation,artifact,justification}.txt`. Preserve legacy labels, whitespace,
Excel active-sheet column mapping C/E/G/J/L/N and F/H/I/K/N/M/O/P/Q.
XML creates blank product templates; its rule version, severity, title,
VulnDiscussion, check-content and fixtext populate the shared baseline.
With `--baseline-only`, create only `<output-root>/<srg>/<rule>/srg.txt`,
for either XML or Excel; preserve existing authored content as in S4.

## Validation and preservation

S3. Validate the entire import before creating output. Require at least one
rule; reject missing XML versions, duplicate rule names (case insensitive),
unsupported namespaces, malformed XML, and invalid Excel ranges
(`1 <= start <= end <= active_sheet.max_row`). Skip Excel rows with blank C.
SRG, product and rule names must be single safe components: ASCII letters,
digits, spaces, underscores, periods and hyphens; start with a letter/digit;
no trailing period/space or consecutive periods; maximum 200 characters.
Reject product names colliding case insensitively with a shared rule name.

S4. Preserve every nonblank existing file byte for byte. Fill missing or
whitespace-only files. Reruns and multiple products share the same baseline.
Reject symlinks and unexpected file/directory types anywhere in the planned
output from the output root downward, before writing. Parent aliases above
the root (such as macOS `/tmp`) are canonicalized. Do not follow output symlinks.
This is a single-user local tool: concurrent modifications of output are
unsupported. Runtime disk/permission failures can leave partial output;
there is no whole-import transaction or rollback.

S5. XML parsing rejects DTDs (including entity declarations), with no external
entity resolution, and limits input to 32 MiB, depth to 128 and element count
to 200,000. No schema validation is promised. Excel requires openpyxl;
XML and `--help` work without it. No credentials, cryptographic operations
or certificate processing are needed.

## Acceptance and SDD/TDD evidence

`python3 -m unittest discover -s scripts/tests -v` exercises S1–S5 through
the executable interface, using temporary directories. Establish RED against
the original copied implementation, implement to GREEN, then run a retained
92-rule VPN fixture in temporary output and compare shared baseline bytes
with the original importer. Do not use existing product projects as test output.
Retain test-stage logs in `/tmp` and record commands/results in the README.

Baseline-only extension (2026-11-04): establish RED for importing without a
product, rerun preservation, conflicting mode flags and Excel baseline
mapping; implement to GREEN. Import the extracted V3R5 VPN XML from `srgs/`
into repository `VPN/`, verify all 92 populated baselines against the source,
then rerun and check that existing files and timestamps are preserved.
