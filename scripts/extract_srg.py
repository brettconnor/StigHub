#!/usr/bin/env python3
"""Extract an SRG ZIP safely. Contract: extract_srg.spec.md."""
import argparse
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unicodedata
import zipfile
import zlib

REPOSITORY = Path(__file__).resolve().parents[1]
MAX_ENTRIES = 10_000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024


def validated_members(archive):
    """Validate paths, member types, aliases and declared resource bounds."""
    infos = archive.infolist()
    if len(infos) > MAX_ENTRIES:
        raise ValueError('Archive exceeds the entry count limit.')
    explicit = set()
    nodes = {}
    members = []
    total = 0
    files = 0
    for info in infos:
        name = info.orig_filename
        trimmed = name[:-1] if info.is_dir() else name
        parts = trimmed.split('/')
        if (not trimmed or '\\' in name or ':' in name
                or any(ord(char) < 32 or ord(char) == 127 for char in name)
                or any(part in ('', '.', '..') for part in parts)):
            raise ValueError(f'Unsafe archive path: {name!r}')
        mode = stat.S_IFMT(info.external_attr >> 16)
        expected = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
        if mode not in (0, expected):
            raise ValueError(f'Unsupported archive entry type: {name!r}')
        if info.is_dir() and info.file_size:
            raise ValueError(f'Directory entries must not carry data: {name!r}')
        if info.flag_bits & 1:
            raise ValueError(f'Encrypted entries are not supported: {name!r}')
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise ValueError(f'Unsupported compression: {name!r}')
        for length in range(1, len(parts) + 1):
            spelling = '/'.join(parts[:length])
            key = unicodedata.normalize('NFC', spelling).casefold()
            is_directory = length < len(parts) or info.is_dir()
            if key in nodes and nodes[key] != (spelling, is_directory):
                raise ValueError(f'Archive path collision: {name!r}')
            nodes[key] = (spelling, is_directory)
        key = unicodedata.normalize('NFC', trimmed).casefold()
        if key in explicit:
            raise ValueError(f'Duplicate archive path: {name!r}')
        explicit.add(key)
        if not info.is_dir():
            files += 1
            total += info.file_size
            if info.file_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                raise ValueError('Archive exceeds decompressed size limits.')
        members.append((info, parts))
    if not files:
        raise ValueError('Archive contains no regular files.')
    return members


def extract_archive(source, destination):
    """Stage and validate everything before publishing; never replace files.

    Intended for a local operator with no concurrent destination modifications.
    Publication-time I/O failures may leave partial output; reruns are safe.
    """
    root = Path(os.path.abspath(destination))
    # Canonicalize trusted system aliases above the chosen output root.
    root = root.parent.resolve() / root.name
    with zipfile.ZipFile(source) as archive, tempfile.TemporaryDirectory(prefix='extract-srg-') as temporary:
        members = validated_members(archive)
        staged = {}
        directories = {root}
        actual_total = 0
        for index, (info, parts) in enumerate(members):
            target = root.joinpath(*parts)
            directories.update(parent for parent in target.parents
                               if parent == root or root in parent.parents)
            if info.is_dir():
                directories.add(target)
                continue
            stage = Path(temporary) / str(index)
            actual_size = 0
            # Reading to EOF also verifies the member's CRC before publication.
            with archive.open(info) as incoming, stage.open('wb') as outgoing:
                while chunk := incoming.read(CHUNK_BYTES):
                    actual_size += len(chunk)
                    actual_total += len(chunk)
                    if actual_size > MAX_FILE_BYTES or actual_total > MAX_TOTAL_BYTES:
                        raise ValueError('Archive exceeds actual decompressed size limits.')
                    outgoing.write(chunk)
            if actual_size != info.file_size:
                raise ValueError(f'Archive member size mismatch: {info.filename!r}')
            staged[target] = stage

        preserved = set()
        for target in sorted(directories | set(staged)):
            if target.is_symlink():
                raise ValueError(f'Destination symlinks are not permitted: {target}')
            if not target.exists():
                continue
            if target in directories:
                if not target.is_dir():
                    raise ValueError(f'Destination directory conflicts with a file: {target}')
            else:
                if not target.is_file():
                    raise ValueError(f'Destination file conflicts with another type: {target}')
                if target.stat().st_size != staged[target].stat().st_size or target.read_bytes() != staged[target].read_bytes():
                    raise ValueError(f'Destination contains a differing file: {target}')
                preserved.add(target)

        # All source and existing-destination checks have passed.
        for directory in sorted(directories, key=lambda p: len(p.parts)):
            directory.mkdir(mode=0o755, parents=True, exist_ok=True)
        extracted = 0
        for target, stage in staged.items():
            if target in preserved:
                continue
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
            with os.fdopen(descriptor, 'wb') as outgoing, stage.open('rb') as incoming:
                shutil.copyfileobj(incoming, outgoing, CHUNK_BYTES)
            extracted += 1
    return extracted, len(preserved)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, f'Error: {message}\n')


def arguments(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument('archive', nargs='?', type=Path,
                        default=REPOSITORY / 'zips/U_VPN_V3R5_SRG.zip',
                        help='ZIP archive (default: repository zips/U_VPN_V3R5_SRG.zip)')
    parser.add_argument('--output-dir', type=Path, default=REPOSITORY / 'srgs',
                        help='Destination (default: repository srgs/)')
    return parser.parse_args(argv)


def main(argv=None):
    try:
        args = arguments(argv)
        extracted, preserved = extract_archive(args.archive, args.output_dir)
        print(f'Done. Extracted {extracted} files; preserved {preserved} identical files '
              f'in {args.output_dir.absolute()}.')
        return 0
    except (OSError, ValueError, RuntimeError, EOFError, zipfile.BadZipFile, zlib.error) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
