#!/usr/bin/env python3
"""Import XML/Excel SRGs without replacing authored StigHub content.

Contract: x2stighub.spec.md. Run --help for options, or run without arguments
for the original interactive workflow.
"""
import argparse
import html
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET
from zipfile import BadZipFile

FIELDS = {
    'requirement': 'F', 'vuldiscussion': 'H', 'status': 'I', 'check': 'K',
    'severity': 'N', 'fix': 'M', 'mitigation': 'O', 'artifact': 'P',
    'justification': 'Q',
}
MAX_XML_BYTES = 32 * 1024 * 1024


class ImportErrorDetail(ValueError):
    """An actionable import or validation error for the operator."""


def text(value):
    return '' if value is None else str(value).strip()


def component(value, label):
    value = text(value)
    if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,199}', value)
            or '..' in value or value.endswith('.')):
        raise ImportErrorDetail(f'{label} must be a nonempty safe directory name: {value!r}')
    return value


class LimitedTreeBuilder(ET.TreeBuilder):
    """Reject DTDs before entities can expand; bound XML structure."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.count = 0

    def start(self, tag, attrs):
        self.depth += 1
        self.count += 1
        if self.depth > 128 or self.count > 200_000:
            raise ImportErrorDetail('XML exceeds depth or element limits.')
        return super().start(tag, attrs)

    def end(self, tag):
        element = super().end(tag)
        self.depth -= 1
        return element

    def doctype(self, name, pubid, system):
        raise ImportErrorDetail('XML DTDs and entity declarations are not permitted.')


def read_xml(source):
    with source.open('rb') as stream:
        data = stream.read(MAX_XML_BYTES + 1)
    if len(data) > MAX_XML_BYTES:
        raise ImportErrorDetail('XML exceeds the 32 MiB size limit.')
    root = ET.fromstring(data, parser=ET.XMLParser(target=LimitedTreeBuilder()))
    namespaces = ['http://checklists.nist.gov/xccdf/' + v for v in ('1.1', '1.2')]
    namespace = next((ns for ns in namespaces if root.tag == f'{{{ns}}}Benchmark'), None)
    if namespace is None:
        raise ImportErrorDetail('Expected an XCCDF 1.1 or 1.2 Benchmark document.')
    ns = {'x': namespace}
    rows = []
    for rule in root.findall('.//x:Rule', ns):
        def field(path):
            element = rule.find(path, ns)
            return '' if element is None else text(''.join(element.itertext()))

        description = rule.find('x:description', ns)
        discussion = ''
        if description is not None:
            nested = next((e for e in description.iter()
                           if e.tag.rsplit('}', 1)[-1].lower() == 'vulndiscussion'), None)
            if nested is not None:
                discussion = text(''.join(nested.itertext()))
            else:
                match = re.search(r'<VulnDiscussion>(.*?)</VulnDiscussion>',
                                  html.unescape(field('x:description')), re.S | re.I)
                if match:
                    discussion = match.group(1).strip()
        rows.append({'name': field('x:version'), 'severity': text(rule.get('severity')),
                     'requirement': field('x:title'), 'vuldiscussion': discussion,
                     'check': field('.//x:check-content'), 'fix': field('x:fixtext')})
    return rows


def read_excel(source, start, end):
    if start is None or end is None or not 1 <= start <= end:
        raise ImportErrorDetail('Excel requires 1 <= start-row <= end-row.')
    try:
        from openpyxl import load_workbook
        from openpyxl.utils.exceptions import InvalidFileException
    except ImportError as exc:
        raise ImportErrorDetail('Excel imports require openpyxl; install scripts/requirements.txt.') from exc
    try:
        workbook = load_workbook(source)
    except (InvalidFileException, KeyError) as exc:
        raise ImportErrorDetail(f'Cannot read Excel workbook: {exc}') from exc
    try:
        sheet = workbook.active
        if sheet is None or end > sheet.max_row:
            raise ImportErrorDetail('Excel end-row exceeds the active worksheet bounds.')
        rows = []
        for number in range(start, end + 1):
            def cell(column):
                return text(sheet[f'{column}{number}'].value)

            name = cell('C')
            if not name:
                continue
            row = {'name': name, 'severity': cell('N'), 'requirement': cell('E'),
                   'vuldiscussion': cell('G'), 'check': cell('J'), 'fix': cell('L')}
            row.update({field + '_file': cell(column) for field, column in FIELDS.items()})
            rows.append(row)
        return rows
    finally:
        workbook.close()


def shared_content(row):
    sections = [('Severity:', 'severity'), ('SRG Requirement:', 'requirement'),
                ('SRG VulDiscussion:', 'vuldiscussion'), ('SRG Check:', 'check'),
                ('SRG Fix:', 'fix')]
    return '\n' + row['name'] + '\n\n' + ''.join(
        f'{label}\n{row.get(field, "")}\n\n' for label, field in sections)


def plan_import(source, srg, product, output_root, start=None, end=None, baseline_only=False):
    """Read and validate the entire source and destination before mutation."""
    srg = component(srg, 'SRG shortname')
    if baseline_only:
        if product is not None:
            raise ImportErrorDetail('--baseline-only cannot be combined with --product.')
    else:
        product = component(product, 'OS/product name')
    if source.suffix.lower() == '.xml':
        if start is not None or end is not None:
            raise ImportErrorDetail('Row ranges apply only to Excel imports.')
        rows = read_xml(source)
    elif source.suffix.lower() == '.xlsx':
        rows = read_excel(source, start, end)
    else:
        raise ImportErrorDetail('Supported input: .xml or .xlsx; extract ZIP archives first.')
    if not rows:
        raise ImportErrorDetail('No rules found in the selected input or row range.')
    seen = set()
    for row in rows:
        row['name'] = component(row['name'], 'Rule version/name')
        name = row['name'].casefold()
        if name in seen:
            raise ImportErrorDetail(f'Duplicate rule version/name: {row["name"]}')
        seen.add(name)
    if not baseline_only and product.casefold() in seen:
        raise ImportErrorDetail('OS/product name collides with a shared rule directory.')

    # Normalize trusted parent aliases such as macOS /tmp -> /private/tmp.
    # The output root itself and every descendant must not be symbolic links.
    root = Path(os.path.abspath(output_root))
    root = root.parent.resolve() / root.name
    plan = {}
    for row in rows:
        plan[root / srg / row['name'] / 'srg.txt'] = shared_content(row)
        if baseline_only:
            continue
        for field in FIELDS:
            content = row.get(field + '_file', '')
            plan[root / srg / product / row['name'] / (field + '.txt')] = (
                f'\n{field.upper()}:\n{content}\n\n' if content else '')
    directories = {root}
    for path in plan:
        directories.update(parent for parent in path.parents if parent == root or root in parent.parents)
    for path in sorted(directories | set(plan)):
        if path.is_symlink():
            raise ImportErrorDetail(f'Output symlinks are not permitted: {path}')
        if path.exists():
            expected_dir = path in directories
            if (expected_dir and not path.is_dir()) or (not expected_dir and not path.is_file()):
                raise ImportErrorDetail(f'Unexpected output file/directory type: {path}')
    return rows, plan


def write_if_blank(path, content):
    """Keep authored bytes; do not follow a final-component symlink."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        pass
    else:
        with os.fdopen(descriptor, 'r', encoding='utf-8', newline='') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ImportErrorDetail(f'Output must be a regular file: {path}')
            if stream.read().strip():
                return False
    # Recheck on the writable descriptor as well, so content that appeared
    # after the read-only check is preserved. Concurrent imports are unsupported.
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o644)
    with os.fdopen(descriptor, 'r+', encoding='utf-8', newline='') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ImportErrorDetail(f'Output must be a regular file: {path}')
        if stream.read().strip():
            return False
        stream.seek(0)
        stream.write(content)
        stream.truncate()
    return True


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, f'Error: {message}\n')


def arguments(argv):
    parser = Parser(description=__doc__)
    parser.add_argument('--input', type=Path, help='Extracted XCCDF XML or Excel workbook')
    parser.add_argument('--srg', help='Shared baseline name, e.g. VPN')
    parser.add_argument('--product', help='OS/product directory, e.g. Cisco-IOS-XE')
    parser.add_argument('--baseline-only', action='store_true',
                        help='Import shared srg.txt files without creating product templates')
    parser.add_argument('--output-root', type=Path, default=Path.cwd())
    parser.add_argument('--start-row', type=int, help='Excel first row, inclusive')
    parser.add_argument('--end-row', type=int, help='Excel last row, inclusive')
    args = parser.parse_args(argv)
    if argv:
        if args.baseline_only and args.product is not None:
            parser.error('--baseline-only cannot be combined with --product.')
        if args.input is None or args.srg is None or (args.product is None and not args.baseline_only):
            parser.error('--input and --srg require either --product or --baseline-only.')
    else:
        print('=== Excel / XML to StigHub ===')
        args.srg = input('Enter the SRG shortname (NDM, WebSrv): ').strip()
        source = input('Enter the Excel or XML file name (with .xlsx or .xml): ').strip()
        if not source:
            raise ImportErrorDetail('Input file is required.')
        args.input = Path(source)
        if args.input.suffix.lower() == '.xlsx':
            args.start_row = int(input('Enter starting row number (e.g., 2): ').strip())
            args.end_row = int(input('Enter ending row number (inclusive): ').strip())
        args.product = input('Enter OS name: ').strip()
    return args


def main(argv=None):
    try:
        args = arguments(sys.argv[1:] if argv is None else argv)
        rows, plan = plan_import(args.input, args.srg, args.product, args.output_root,
                                 args.start_row, args.end_row, baseline_only=args.baseline_only)
        written = 0
        for path, content in plan.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            written += write_if_blank(path, content)
        print(f'Done. Processed {len(rows)} rules; wrote {written} files; '
              f'preserved {len(plan) - written} nonblank files.')
        return 0
    except (ValueError, OSError, ET.ParseError, BadZipFile, EOFError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
