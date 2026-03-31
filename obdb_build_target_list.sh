#!/usr/bin/env bash
set -eo pipefail

ORG="OBDb"
OUT_DIR="data/"
OUT_FILE="${OUT_DIR}/obdb-repositories.txt"

if ! [ -d "$OUT_DIR" ] ; then
    echo "must be runned from repo root folder"
    exit 1
fi

special_repo() {
    case "$1" in
        .github|.meta|.vehicle-template|.make-template)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

repo_has_signalsets() {
    local repo="$1"
    gh api "repos/${ORG}/${repo}/contents/signalsets" >/dev/null 2>&1
}

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

while IFS= read -r repo; do
    [ -n "$repo" ] || continue

    if special_repo "$repo"; then
        echo "skip special repo: $repo"
        continue
    fi

    if ! repo_has_signalsets "$repo"; then
        echo "skip without signalsets/: $repo"
        continue
    fi

    echo "keep: $repo"
    printf '%s\n' "$repo" >> "$tmp_file"
done < <(gh repo list "$ORG" --limit 1000 --json name -q '.[].name')

sort -u "$tmp_file" > "$OUT_FILE"

echo "written: $OUT_FILE"