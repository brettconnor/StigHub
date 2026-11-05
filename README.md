# StigHub-dev

StigHub-dev is a local working repository for DISA Security Requirements
Guides (SRGs) and the product-specific implementation guidance used to assess
network devices. It contains a VPN SRG baseline, product folders for Cisco
platforms, helper scripts for viewing and importing SRG content, and a sample
IOS-XE site-to-site IPsec configuration.

The repository is a content-authoring workspace, not a device-management
application. The scripts do not connect to devices or publish content.

## Quickstart for operators

These steps are intended for a new human operator who wants to inspect the
baseline or begin editing product guidance.

### Requirements

- Python 3.8 or newer for the import and extraction tools.
- Bash 3.2 or newer for the viewer (the macOS system Bash is supported).
- `uv` is optional and can provide an isolated environment for running tests.
- Excel workbook imports require `openpyxl`; XML imports and ZIP extraction
  use only the Python standard library.

### 1. Check out the repository and inspect local changes

Use the repository root as the working directory:

```sh
cd /path/to/StigHub-dev
git status --short
```

Do not overwrite or discard existing changes without confirming they are
disposable. Some SRG source archives, extracted source files, Python
environments, and Cisco product-template directories are ignored by Git; see
[Files and Git ignore behavior](#files-and-git-ignore-behavior).

### 2. Open a rule

Each shared VPN rule is identified by its DISA rule ID. For example:

```sh
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040 Cisco-IOS-XE
```

The viewer prints the shared `srg.txt` baseline followed by the selected
product's `.txt` files. In a terminal it uses `less -FX` when available. To
print directly or save the output:

```sh
scripts/stig-view.sh --root VPN --no-pager SRG-NET-000019-VPN-000040 Cisco-IOS-XE
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040 Cisco-IOS-XE > /tmp/rule-review.txt
```

To see all options or view from a product directory:

```sh
scripts/stig-view.sh --help
```

### 3. Edit product guidance

Product-specific guidance lives in:

```text
VPN/<product>/<rule-id>/
```

The expected files are `requirement.txt`, `vuldiscussion.txt`, `status.txt`,
`check.txt`, `severity.txt`, `fix.txt`, `mitigation.txt`, `artifact.txt`, and
`justification.txt`. Edit these files in the normal text editor. Keep the
shared DISA requirement in `VPN/<rule-id>/srg.txt`; product folders describe
how the product's configuration meets the requirement.

Use the rule viewer after editing to review the baseline and product guidance
together. Confirm the rule ID and product name before adding or moving files.

### 4. Run the tests before handing off changes

The tests use Python's standard library plus `openpyxl` for workbook cases.
With `uv`, run the suite from the repository root:

```sh
uv run --no-project --with-requirements scripts/requirements.txt \
  python -m unittest discover -s scripts/tests -v
bash -n scripts/stig-view.sh
```

Alternatively, install the listed requirement in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
.venv/bin/python -m unittest discover -s scripts/tests -v
bash -n scripts/stig-view.sh
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `VPN/<rule-id>/srg.txt` | Shared source baseline for a rule. |
| `VPN/<product>/<rule-id>/*.txt` | Product implementation, check, and evidence fields. |
| `configs/cli/iosxe-ikev2-ipsec` | Example IOS-XE site-to-site IPsec configuration with placeholders. |
| `scripts/stig-view.sh` | Read-only viewer for a shared baseline and product files. |
| `scripts/x2stighub.py` | Imports XCCDF XML or Excel SRG content into the repository layout. |
| `scripts/extract_srg.py` | Safely extracts the SRG ZIP archive into a source directory. |
| `scripts/tests/` | Acceptance tests for the scripts. |
| `scripts/*.spec.md` | Behavioral contracts for the scripts. |
| `scripts/README.md` | More detailed script usage and verification notes. |
| `srgs/` | Local extracted source bundle, when available. |
| `zips/` | Local source ZIP archive, when available. |

The layout supports a shared baseline with one or more product-specific
interpretations. For XML imports, the importer populates the shared
`srg.txt` and creates blank product templates. For Excel imports, product
fields are imported using the workbook's established column mapping.

## Common operator workflows

### Read an existing baseline or product rule

```sh
# Shared baseline only
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040

# Shared baseline plus Cisco IOS-XE product files
scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040 Cisco-IOS-XE
```

The viewer accepts a selected root with `--root`; without it, paths are
relative to the current directory. With no rule argument it displays
`srg.txt` directly under the selected root. Product mode includes regular,
non-hidden `.txt` files in filename order, including empty templates.
`--no-pager` disables terminal paging. The viewer does not edit files.

### Extract the SRG source archive

When the approved source archive is available at the repository's default
location, extract it with:

```sh
python3 scripts/extract_srg.py
```

By default this reads `zips/U_VPN_V3R5_SRG.zip` and extracts into `srgs/`.
The archive can be supplied explicitly, and the destination can be changed:

```sh
python3 scripts/extract_srg.py /path/to/approved-srg.zip --output-dir /tmp/srg-source
```

The extractor validates archive paths and entry types, checks CRCs, rejects
unsupported or oversized archives, and stages the archive before publishing
files. Identical existing files are preserved. A conflicting existing file
causes an error rather than an overwrite. It uses Python's standard library.
The output directory can be partially populated if the filesystem fails
during publication; rerunning is safe after resolving the underlying issue.

If the ZIP is not present locally, obtain it from the project's approved
source and follow the project's data-handling requirements. The repository
does not download source archives automatically.

### Import an XCCDF XML source

The source bundle includes an XCCDF XML file at
`srgs/U_VPN_V3R5_Manual_SRG/U_VPN_SRG_V3R5_Manual-xccdf.xml` when extracted.
To import only the shared baseline:

```sh
python3 scripts/x2stighub.py \
  --input srgs/U_VPN_V3R5_Manual_SRG/U_VPN_SRG_V3R5_Manual-xccdf.xml \
  --srg VPN \
  --baseline-only \
  --output-root .
```

To import the shared baseline and create templates for a product:

```sh
python3 scripts/x2stighub.py \
  --input srgs/U_VPN_V3R5_Manual_SRG/U_VPN_SRG_V3R5_Manual-xccdf.xml \
  --srg VPN \
  --product Cisco-IOS-XE \
  --output-root .
```

XML product templates are intentionally blank; the baseline contains the
source requirements. Choose `--baseline-only` when you do not want product
templates. Do not combine `--baseline-only` and `--product`.

The importer validates the complete input and output plan before writing.
It preserves nonblank existing files byte-for-byte, and fills only missing
or whitespace-only files. This is intentionally conservative: it will not
refresh authored baselines when the source changes. Review its output and
the resulting Git status before continuing.

### Import an Excel workbook

Excel import requires `openpyxl`, listed in `scripts/requirements.txt`.
Create an isolated environment if needed:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
```

Supply the workbook and inclusive row range. Example:

```sh
.venv/bin/python scripts/x2stighub.py \
  --input /path/to/approved-srg.xlsx \
  --srg VPN \
  --product Cisco-IOS-XE \
  --start-row 2 \
  --end-row 93 \
  --output-root .
```

Use the actual active-sheet range in the workbook. Rows with a blank rule
name in column C are skipped. The baseline reads the rule name from C,
requirement from E, discussion from G, check from J, fix from L, and severity
from N. Product files use F (requirement), H (discussion), I (status), K
(check), N (severity), M (fix), O (mitigation), P (artifact), and Q
(justification). An Excel baseline-only import is also available by
replacing `--product` with `--baseline-only`.

For interactive use, run `python3 scripts/x2stighub.py` without arguments.
For unattended use, provide the full set of required command-line options;
partial configurations fail rather than unexpectedly prompting.

## Content model and authoring guidance

### Shared baseline

The shared baseline is one `srg.txt` per rule under the selected SRG directory
(currently `VPN/`). The importer uses the rule version/name as the directory
name and writes source material such as severity, requirement, discussion,
check content, and fix text. Treat this as the common requirement, not as a
product's evidence that it is compliant.

### Product-specific files

Each product has a directory under the SRG, for example `Cisco-IOS-XE/`.
Product files should explain the product-specific implementation and review
evidence. The importer may create blank files for XML imports or populate
files from Excel. Manually authored nonblank content takes precedence during
subsequent imports.

### File naming and validation

The scripts expect rule, SRG, and product names to be safe single directory
components. Avoid slashes, control characters, path traversal, and ambiguous
names. The importer supports XCCDF 1.1 and 1.2 XML and `.xlsx` workbooks;
ZIPs must be extracted before import. XML DTDs are rejected, and parser input
and structure are bounded. The importer does not claim XSD/schema validation.

## Files and Git ignore behavior

The root `.gitignore` excludes Python cache/virtual-environment artifacts,
`zips/`, `srgs/`, `.DS_Store`, and `/VPN/Cisco-*/`. The ZIP and extracted
vendor source are local input data, while the Cisco product directories are
currently treated as generated/local content by that ignore rule.

Before handing off or committing changes, check both ordinary and ignored
files:

```sh
git status --short
git status --short --ignored
git check-ignore -v VPN/Cisco-IOS-XE/SRG-NET-000019-VPN-000040/check.txt
```

Ignored data does not appear in ordinary `git status` output. Do not assume
an import or edit will be committed just because the file exists locally.
If a product directory must become version-controlled, first agree on the
repository's intended tracking policy and then make a deliberate,
reviewed `.gitignore` change. Do not force-add large vendor source bundles
or ignored generated trees without approval.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `No such file` for the default ZIP or XML | Obtain the approved source archive and extract it with `scripts/extract_srg.py`; source-data directories are ignored and may not exist in a clean clone. |
| `Excel imports require openpyxl` | Install `scripts/requirements.txt` in the Python environment used to run the importer. |
| Import reports an existing file conflict or invalid output type | Inspect the named path and preserve authored content. The importer deliberately does not overwrite nonblank files or follow symlinks. |
| Changes do not appear in `git status` | Check `git status --short --ignored` and `git check-ignore -v <path>`; the path may match an ignore rule. |
| Viewer reports a missing baseline or product | Confirm the rule ID, `--root`, and product spelling, and verify that the expected directory and `srg.txt` exist. |
| A ZIP extraction fails | Verify the source archive and destination, resolve any conflicting destination files, then rerun. The extractor does not replace differing files. |

The contracts and complete tool-specific notes are in
[`scripts/README.md`](scripts/README.md) and the `scripts/*.spec.md` files.
