#!/usr/bin/env python3
"""Post-build checks for a migrated .docx.

Fails (exit 1) on: an input that changed, an output that does not open,
tracked changes, comments, or marking/forbidden-text hits.
Warns on: remaining placeholders, remaining highlighted text, and an output
identical to an input. --strict turns warnings into failures.

The output is never modified. See verify.spec.md for the behavior contract.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import (DEFAULT_MARKING_PATTERNS, DEFAULT_PLACEHOLDER_PATTERNS,  # noqa: E402
                       DocxError, scan, sha256_file)


def verify(output, unchanged=(), forbid=(), use_default_patterns=True, placeholder_patterns=(),
           strict=False, allow_revisions=False, allow_comments=False):
    """Return (status, checks, scan_result). status is 'PASS' or 'FAIL'."""
    checks = []

    def add(level, name, detail, items=None):
        checks.append({'level': level, 'check': name, 'detail': detail, 'items': items or []})

    out_path = Path(output)
    out_sha = None
    if out_path.is_file():
        out_sha = sha256_file(out_path)

    # 1. inputs unchanged
    for path, expected in unchanged:
        p = Path(path)
        if out_path.exists() and p.exists() and p.resolve() == out_path.resolve():
            raise DocxError('--unchanged path is the output itself: %s' % path)
        if not p.is_file():
            add('FAIL', 'input unchanged', 'missing: %s' % path)
            continue
        actual = sha256_file(p)
        if actual.lower() != expected.lower():
            add('FAIL', 'input unchanged', '%s: sha256 %s != expected %s' % (path, actual, expected))
        else:
            add('PASS', 'input unchanged', path)
        if out_sha and out_sha == actual:
            add('WARN', 'output differs from input', 'output is byte-identical to %s' % path)

    # 2. output opens
    patterns = (list(DEFAULT_MARKING_PATTERNS) if use_default_patterns else []) + list(forbid)
    phs = list(DEFAULT_PLACEHOLDER_PATTERNS) + list(placeholder_patterns)
    try:
        res = scan(out_path, patterns, phs)
    except DocxError as exc:
        add('FAIL', 'output opens', str(exc))
        return 'FAIL', checks, None
    try:
        import docx  # noqa: F401
    except ImportError:
        add('WARN', 'output opens', 'package and XML OK; python-docx not installed, load not tested')
    else:
        try:
            docx.Document(str(out_path))
            add('PASS', 'output opens', 'package, XML parts and python-docx load OK')
        except Exception as exc:  # noqa: BLE001 - report any loader failure
            add('FAIL', 'output opens', 'python-docx failed to load: %s' % exc)

    # 3. tracked changes / comments
    tc = res['tracked_changes']
    n = sum(tc['counts'].values())
    if n:
        add('WARN' if allow_revisions else 'FAIL', 'no tracked changes',
            '%d revision elements, authors: %s' % (n, ', '.join(tc['authors']) or 'unknown'),
            ['%s %s by %s: %s' % (i['loc'], i['type'], i['author'], i['text']) for i in tc['items']])
    else:
        add('PASS', 'no tracked changes', 'none')
    cm = res['comments']
    if cm['count'] or cm['references']:
        add('WARN' if allow_comments else 'FAIL', 'no comments',
            '%d comments, %d references' % (cm['count'], cm['references']),
            ['%s: %s' % (c['author'], c['text']) for c in cm['items']])
    else:
        add('PASS', 'no comments', 'none')

    # 4. markings / forbidden text
    if res['markings']:
        add('FAIL', 'no markings/forbidden text', '%d hits' % len(res['markings']),
            ['%s %r: %s' % (m['loc'], m['match'], m['context']) for m in res['markings']])
    else:
        add('PASS', 'no markings/forbidden text', '%d patterns checked' % len(patterns))

    # 5. placeholders / highlight
    lvl = 'FAIL' if strict else 'WARN'
    if res['placeholders']:
        add(lvl, 'placeholders remaining', '%d' % len(res['placeholders']),
            ['%s %s' % (p['loc'], p['text']) for p in res['placeholders']])
    else:
        add('PASS', 'placeholders remaining', 'none')
    if res['highlights']:
        add(lvl, 'highlighted text remaining', '%d paragraphs' % len(res['highlights']),
            ['%s %r' % (h['loc'], h['color_runs']) for h in res['highlights']])
    else:
        add('PASS', 'highlighted text remaining', 'none')

    # 6. info
    props = res['properties']
    add('INFO', 'file properties', 'creator=%s; lastModifiedBy=%s; title=%s' % (
        props.get('core.creator'), props.get('core.lastModifiedBy'), props.get('core.title')))
    add('INFO', 'headers/footers', ' || '.join(
        '%s: %s' % (h['part'], ' | '.join(h['text'])) for h in res['headers_footers'] if h['text']) or 'none')
    add('INFO', 'output sha256', out_sha or '?')

    status = 'FAIL' if any(c['level'] == 'FAIL' for c in checks) else 'PASS'
    return status, checks, res


def render(status, checks):
    lines = []
    for c in checks:
        lines.append('%-4s  %-28s %s' % (c['level'], c['check'], c['detail']))
        for it in c['items']:
            lines.append('        - %s' % it)
    lines.append('')
    lines.append('RESULT: %s' % status)
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Verify a migrated .docx.')
    ap.add_argument('--output', required=True, help='the migrated .docx to check')
    ap.add_argument('--unchanged', nargs=2, action='append', default=[], metavar=('PATH', 'SHA256'),
                    help='an input that must still have this SHA-256 (template, source); repeatable')
    ap.add_argument('--forbid', action='append', default=[], metavar='REGEX',
                    help='case-insensitive pattern that must not appear (e.g. source-only org names); repeatable')
    ap.add_argument('--no-default-patterns', action='store_true',
                    help='do not use the built-in marking patterns')
    ap.add_argument('--placeholder', action='append', default=[], metavar='REGEX',
                    help='extra placeholder pattern; repeatable')
    ap.add_argument('--strict', action='store_true', help='remaining placeholders/highlights fail')
    ap.add_argument('--allow-revisions', action='store_true', help='tracked changes warn instead of fail')
    ap.add_argument('--allow-comments', action='store_true', help='comments warn instead of fail')
    ap.add_argument('--json', action='store_true', help='print JSON')
    args = ap.parse_args(argv)
    for _, sha in args.unchanged:
        if not re.fullmatch(r'[0-9a-fA-F]{64}', sha):
            print('error: not a SHA-256 hex digest: %s' % sha, file=sys.stderr)
            return 2
    try:
        for p in args.forbid + args.placeholder:
            re.compile(p)
    except re.error as exc:
        print('error: invalid regex: %s' % exc, file=sys.stderr)
        return 2
    if not Path(args.output).is_file():
        print('error: output not found: %s' % args.output, file=sys.stderr)
        return 2
    try:
        status, checks, _ = verify(args.output, args.unchanged, args.forbid, not args.no_default_patterns,
                                   args.placeholder, args.strict, args.allow_revisions, args.allow_comments)
    except DocxError as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({'result': status, 'checks': checks}, indent=1))
    else:
        print(render(status, checks))
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
