# CLI STIG viewer specification

Contract established before implementation, 2026-11-04.

V1. Provide executable Bash 3.2-compatible `stig-view.sh`. Preserve legacy
positional modes: zero arguments reads `./srg.txt`; one rule ID reads
`./<rule>/srg.txt`; rule ID plus product reads the shared baseline followed
by that product's `./<product>/<rule>/*.txt`. Default root is the working
directory; `--root DIRECTORY` selects another root. `--no-pager` forces plain
output. `-h`/`--help` documents all modes and returns 0. Reject unknown options,
missing option values and excess positional arguments with `Error:` on stderr
and a nonzero exit. Support `--` to end option parsing.

V2. Preserve baseline bytes without a header. In two-argument mode, append
all regular, nonhidden `.txt` product files in C-locale filename order, each
preceded by a blank line and `===== <filename> =====` on its own line. Include
headers for blank templates. Ignore other extensions and subdirectories.
An existing empty product directory is valid and displays only the baseline.
Do not create or modify repository files.

V3. Require existing readable regular baseline/product files and an existing
product directory when requested. Validate all selected inputs before rendering
so a missing product or invalid file does not emit a partial baseline. Reject
symlinks at the explicitly selected root, baseline file, and descendant
directories or selected `.txt` files. Trusted aliases above the root are
canonicalized. Rule/product IDs are single safe components: ASCII letters,
digits, spaces, underscores, hyphens and periods; start with a letter/digit;
at most 200 characters; no consecutive periods or trailing period/space.
Never evaluate IDs, paths, filenames, file contents or PAGER as shell code.
The viewer assumes no concurrent filesystem modifications.

V4. When stdout is a terminal, use `less -FX` if available unless `--no-pager`
is set. Disable less preprocessing hooks/history and shell features; ignore
PAGER and inherited LESS options. Otherwise stream to stdout. Preserve command
failures, report output failure, and treat renderer SIGPIPE after an early
pager exit as normal. Plain output is the source text, including any control
characters; this is a local viewer, not a terminal-text sanitizer.

## SDD/TDD acceptance

Write tests first, copy the original as the starting implementation, and run
RED. Implement to GREEN using Python unittest to exercise Bash, real temporary
baseline/product files and a pseudoterminal with a test pager. Run the complete
repository test suite under uv and `bash -n`. Verify real VPN output for all
92 rules and all three Cisco products without changing source/project files.
Retain stage logs and verification in `/tmp` and document usage in README.md.
