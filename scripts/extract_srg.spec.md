# SRG ZIP extraction specification

Contract established before implementation, 2026-11-04.

E1. `extract_srg.py [ARCHIVE] [--output-dir DIRECTORY]` extracts ZIP contents
with their original relative paths. Defaults are repository-relative
`zips/U_VPN_V3R5_SRG.zip` and `srgs`, independent of working directory.
Use Python's standard library only; support `uv run --no-project` and Python.
Success exits 0 and reports extracted/preserved file counts and destination.
Failures exit nonzero with `Error:` and no traceback. Help exits 0.

E2. Preserve existing identical files byte for byte; reruns succeed without
rewriting them. Refuse any existing differing file or file/directory conflict
before publishing any new files. Preserve unrelated destination contents.
Ignore archive permissions, ownership and timestamps: create ordinary writable
directories and files, even if archive directories are read-only. Do not import
the extracted XML or change any StigHub product projects.

E3. Before publishing, validate every member, fully decompress it and check
its CRC in temporary staging. Reject absolute paths, drive/colon paths,
backslashes, NUL/control characters, empty/dot/dot-dot path segments,
symlinks and special file entries, directory entries carrying data,
duplicate paths and file/parent collisions.
Detect case-insensitive and Unicode-normalized path aliases as collisions.
Reject destination symlinks from the output root downward. Canonicalize
trusted parent aliases above the root, such as macOS `/tmp`.

E4. Reject missing, malformed, corrupt, encrypted, empty (no regular files),
and unsupported-compression archives. Support stored and deflated entries.
Bounds: at most 10,000 entries, 64 MiB per file, 256 MiB decompressed total;
enforce declared sizes before staging and actual sizes during streaming.
Validation failures leave the destination untouched and remove temporary
staging. A publication-time disk/permission error may leave partial output;
there is no whole-extraction transaction. Concurrent destination edits are
unsupported. Never overwrite an existing file during publication.

## Acceptance evidence

Write executable acceptance tests for E1–E4, run RED before creating the
implementation, then implement to GREEN. Run the complete suite with uv,
then use the script on the requested archive and compare every extracted
file byte for byte with its ZIP member. Retain RED/GREEN and real-archive
verification under `/tmp`; document usage and results in scripts/README.md.
