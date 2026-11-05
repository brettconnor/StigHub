# StigHub scripts

## View shared rules and product guidance

`stig-view.sh` is a read-only Bash viewer. From the repository root, view a
shared VPN rule and optionally its product guidance:

```sh
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040 Cisco-IOS-XE
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040 Cisco-ASA
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040 Cisco-Secure-Firewall
```

The shared `srg.txt` is displayed first. Product `.txt` files follow in
filename order with labels, including labels for currently blank templates.
Other extensions and subdirectories are ignored. Without positional arguments,
the viewer reads `srg.txt` in the current directory (or the selected `--root`).
Without `--root`, named rules/products are relative to the working directory.

Interactive terminal output uses `less -FX` when available. Redirected output
is plain text; use `--no-pager` to force plain output in a terminal:

```sh
scripts/stig-view.sh --root VPN --no-pager SRG-NET-000019-VPN-000040 Cisco-ASA
scripts/stig-view.sh --help
```

Run this Bash script directly; it needs no Python environment. Missing files,
unsafe IDs, symlinks and invalid arguments return a nonzero exit with an error.
All selected paths are checked before rendering. The viewer does not edit
project files. Concurrent filesystem changes are unsupported, and plain
output preserves control characters present in the source text.

The contract is [stig-view.spec.md](stig-view.spec.md). The initial 15-test
RED run against the copied original had 23 failures including subtests.
The rewritten viewer passes 18 acceptance tests covering legacy modes,
product labels, path validation, terminal paging, early pager exit, fallback
without less, and command failures. All 55 repository tests pass under uv.
Syntax was checked with macOS `/bin/bash` 3.2. CodeGuard review covers quoted
command arguments, path validation and read-only file handling. PAGER is
never evaluated; less preprocessing hooks, shell features and history are
disabled. No credentials, cryptography or certificate handling were added.
Real-project verification passed 368 invocations: all 92 shared VPN rules
alone and with each of the three Cisco products. All 2,576 project files
retained their contents and modification times; the original Bash script
is unchanged. RED/GREEN logs, a sample and verification are retained at
`/tmp/stig-view-sdd-tdd-dddce1lp/`.

## Extract SRG archives

`extract_srg.py` extracts the VPN archive from `zips/` into `srgs/`, preserving
its internal layout. It needs only Python's standard library. Defaults are
relative to this repository, so the script works from any working directory:

```sh
uv run --no-project /Users/brettcon/git/StigHub-dev/scripts/extract_srg.py
```

From the repository root, choose a different archive or output directory:

```sh
uv run --no-project scripts/extract_srg.py zips/U_VPN_V3R5_SRG.zip --output-dir srgs
```

Identical existing files are preserved without changing their timestamps.
A differing existing file causes an error before publishing any archive
contents. Unrelated destination files remain untouched. Archived read-only
directory modes are ignored so extracted directories remain writable.
Archive paths, links, duplicates, decompressed sizes and CRCs are validated
before publication. Concurrent destination edits are unsupported; a disk or
permission failure during publication may leave partial output.

The contract is [extract_srg.spec.md](extract_srg.spec.md). SDD/TDD evidence:
the initial 14-test RED run failed before implementation; a later regression
test also failed before rejecting directory entries carrying data. All
16 extractor tests and 17 importer tests now pass under uv:

```sh
uv run --no-project --with-requirements scripts/requirements.txt \
  python -m unittest discover -s scripts/tests -v
```

Actual extraction verified all six VPN files byte for byte against the ZIP.
A rerun preserved all six files and their timestamps. RED/GREEN logs and
verification are retained at `/tmp/extract-srg-sdd-tdd-68rl_ldl/`.
CodeGuard file-handling and input-validation checks informed the extractor;
it has no credentials, certificate handling, cryptography or network calls.

## Import extracted XML or Excel

`x2stighub.py` imports an extracted XCCDF XML document or an Excel workbook
into the shared baseline and product layout. XML imports need only Python's
standard library. For Excel, install the dependency in an environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
```

From the repository root, run the importer without arguments for interactive
prompts, or use explicit options. To create and populate only the shared VPN
baseline from the extracted XML:

```sh
uv run --no-project scripts/x2stighub.py \
  --input srgs/U_VPN_V3R5_Manual_SRG/U_VPN_SRG_V3R5_Manual-xccdf.xml \
  --srg VPN --baseline-only --output-root .
```

This writes `VPN/<rule>/srg.txt` with severity, requirement, discussion,
check and fix from the source. It does not need a product name.
`--baseline-only` and `--product` cannot be combined.

To add a product's nine template files per rule alongside the shared baseline:

```sh
python3 scripts/x2stighub.py \
  --input srgs/U_VPN_V3R5_Manual_SRG/U_VPN_SRG_V3R5_Manual-xccdf.xml \
  --srg VPN \
  --product Cisco-IOS-XE \
  --output-root .
```

Repeat with `--product Cisco-Secure-Firewall` for the second product. Excel
imports also require `--start-row 2 --end-row 93` (use the actual worksheet
range). Row numbers are inclusive; the active worksheet is used. ZIP archives
must be extracted first. Relative input/output paths are relative to the
working directory, not to the script.

Each rule creates `VPN/<rule>/srg.txt` plus nine product files under
`VPN/<product>/<rule>/`. XML product files are intentionally blank; the
shared baseline holds the source requirements. Excel imports populate
product files from the existing workbook column mapping. Product guidance
must be authored separately. Existing nonblank files, including read-only
authored files, are preserved byte for byte. Missing or whitespace-only files
are filled. A changed source does not refresh a populated baseline.

Validation rejects unsafe path components, symlink outputs, empty imports,
duplicates, unsupported XML namespaces, DTDs, and invalid Excel ranges.
Source and destination validation completes before output writes begin.
The tool supports local single-user use; concurrent output edits are
unsupported. Disk or permission errors during writes may leave partial
output. Inspect the error and rerun after resolving the cause.

## Specification and tests

The implementation contract is [x2stighub.spec.md](x2stighub.spec.md).
Acceptance tests exercise the executable interface and map to S1–S5.
Install the Excel dependency before running the complete suite:

```sh
python3 -m unittest discover -s scripts/tests -v
```

SDD/TDD evidence retained from 2026-11-04:

- Wrote the specification and initial 12 acceptance tests, then copied the
  original importer as the starting implementation. The RED run failed with
  22 failures (including subtests): `/tmp/x2stighub-tdd-red.log`.
- Implemented the contract and added boundary cases for XML resource limits,
  UTF-16 DTDs, filesystem conflicts, missing sources and dependency-free XML.
- Added a preservation test for read-only authored files. It failed before
  the fix: `/tmp/x2stighub-tdd-readonly-red.log`.
- Final GREEN: 17 tests pass; `/tmp/x2stighub-tdd-green.log`.
- Real VPN fixture: all 92 rules, 920 baseline/first-product files matching
  the original byte for byte, and two products with 828 templates apiece.
  Outputs and verification: `/tmp/x2stighub-sdd-tdd-xcihe3bl/`.
  All 2,576 existing VPN files and the original Python script were unchanged.

Temporary evidence is local and may be removed by the operating system;
the specification and acceptance tests remain in the repository.

CodeGuard review covered file handling, XML parsing and input validation.
DTD rejection occurs in the parser callback, including UTF-16 input; XML
size, depth and element limits are tested. No credentials, certificate
handling or cryptographic operations are present. The script introduces
no network calls. XML schema validation is outside this contract.

Baseline-only extension validation (2026-11-04): specification and four
acceptance tests preceded implementation. RED had three failing tests;
the conflicting-mode rejection already failed safely. GREEN now has 37
passing tests across importer and extractor. The repository `VPN/` contains
92 shared rule files, with every field verified against the extracted XML.
A rerun wrote zero files and preserved all 92 files and their timestamps.
Logs and verification: `/tmp/vpn-baseline-sdd-tdd-3lnoq_ge/`.
