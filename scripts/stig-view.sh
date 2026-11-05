#!/bin/bash
# Read-only STIG viewer. Contract: stig-view.spec.md. Compatible with Bash 3.2.
set -o pipefail
export LC_ALL=C

print_help() {
    cat <<'EOF'
DISA STIG/SRG command-line viewer

Usage: stig-view.sh [--root DIRECTORY] [--no-pager] [RULE_ID [PRODUCT]]

  No positional arguments: display srg.txt directly under the selected root.
  RULE_ID: display <root>/<rule>/srg.txt.
  RULE_ID PRODUCT: also display <root>/<product>/<rule>/*.txt, with file labels.

Options:
  --root DIRECTORY  Baseline directory (default: current working directory).
  --no-pager        Stream text directly, including when stdout is a terminal.
  -h, --help        Show this help.
  --               End option parsing.

Terminal output uses less -FX when available; redirected output is plain text.

Example from the StigHub-dev repository root:
  scripts/stig-view.sh --root VPN SRG-NET-000019-VPN-000040 Cisco-IOS-XE
EOF
}

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

valid_component() {
    local value="$1"
    [[ -n "$value" && ${#value} -le 200 && "$value" != *..* &&
       "$value" != *. && "$value" != *' ' &&
       "$value" =~ ^[A-Za-z0-9][A-Za-z0-9\ ._-]*$ ]]
}

check_directory() {
    [[ ! -L "$1" && -d "$1" && -r "$1" && -x "$1" ]] ||
        fail "Expected a readable directory without a symlink: $1"
}

check_file() {
    [[ ! -L "$1" && -f "$1" && -r "$1" ]] ||
        fail "Expected a readable regular file without a symlink: $1"
}

root=$(pwd -P) || fail 'Cannot determine the working directory.'
no_pager=false
positional=()
while (( $# )); do
    case "$1" in
        -h|--help) print_help; exit 0 ;;
        --root)
            (( $# >= 2 )) || fail '--root requires a directory.'
            [[ -n "$2" ]] || fail '--root requires a nonempty directory.'
            root="$2"
            shift 2
            ;;
        --no-pager) no_pager=true; shift ;;
        --)
            shift
            while (( $# )); do
                positional+=("$1")
                shift
            done
            ;;
        -*) fail "Unknown option: $1" ;;
        *) positional+=("$1"); shift ;;
    esac
done
(( ${#positional[@]} <= 2 )) || fail 'Expected at most RULE_ID and PRODUCT.'
for value in "${positional[@]}"; do
    valid_component "$value" || fail "Invalid rule/product directory name: $value"
done
# Remove trailing slashes so an explicitly selected symlink remains detectable.
while [[ "$root" != / && "$root" == */ ]]; do
    root=${root%/}
done
check_directory "$root"
root=$(cd -P -- "$root" && pwd -P) || fail 'Cannot resolve the selected root.'

baseline="$root/srg.txt"
if (( ${#positional[@]} >= 1 )); then
    rule=${positional[0]}
    check_directory "$root/$rule"
    baseline="$root/$rule/srg.txt"
fi
check_file "$baseline"
files=("$baseline")
if (( ${#positional[@]} == 2 )); then
    product=${positional[1]}
    check_directory "$root/$product"
    product_dir="$root/$product/$rule"
    check_directory "$product_dir"
    shopt -s nullglob
    for file in "$product_dir"/*.txt; do
        [[ ! -L "$file" ]] || fail "Product text files must not be symlinks: $file"
        [[ -d "$file" ]] && continue
        check_file "$file"
        files+=("$file")
    done
fi

render() {
    local index
    cat -- "${files[0]}" || return $?
    for (( index=1; index<${#files[@]}; index++ )); do
        printf '\n===== %s =====\n' "${files[index]##*/}" || return $?
        cat -- "${files[index]}" || return $?
    done
}

if [[ -t 1 && "$no_pager" == false ]] && command -v less >/dev/null 2>&1; then
    # Fixed arguments; never evaluate PAGER or run less preprocessing hooks.
    render | LESSSECURE=1 LESSOPEN= LESSCLOSE= LESS= LESSHISTFILE=- \
        LESSKEY=/dev/null LESSKEYIN=/dev/null command less -FX
    status=$?
    # A user quitting the pager can close the pipe before rendering completes.
    [[ "$status" == 141 ]] && status=0
else
    render
    status=$?
fi
(( status == 0 )) || fail "Unable to display the selected files (exit $status)."
exit 0
