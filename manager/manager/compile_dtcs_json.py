#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path

DEFAULT_MANUFACTURER = "generic"
NULL_NODE = "_"

def norm_code(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip().upper()
    m = re.fullmatch(r"[PCBU][0-3][0-9A-F]{3}", s)
    if m:
        return s
    m = re.search(r"\b([PCBU][0-3][0-9A-F]{3})\b", s)
    return m.group(1) if m else None

def node_name(v: str | None) -> str:
    s = (v or "").strip()
    return s if 0 < len(s) else NULL_NODE

def load_desc_ini(path: Path) -> dict[str, str | None]:
    meta: dict[str, str | None] = {"manufacturer": DEFAULT_MANUFACTURER, "engine": None, "ecu": None}
    if not path.exists():
        return meta
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().lower()
        v = v.strip()
        if k in meta:
            meta[k] = v or None
    return meta

def parse_json(path: Path, manufacturer: str, engine_model: str | None, ecu_model: str | None) -> list[tuple[str, str, str, str | None, str | None]]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    out: list[tuple[str, str, str, str | None, str | None]] = []

    def add(code, desc):
        c = norm_code(code)
        if c and desc:
            out.append((c, str(desc).strip(), manufacturer, engine_model, ecu_model))

    if isinstance(data, dict):
        if all(isinstance(k, str) for k in data.keys()) and any(norm_code(k) for k in data.keys()):
            for k, v in data.items():
                add(k, v)
            return out

        for _, v in data.items():
            if isinstance(v, list):
                for it in v:
                    if isinstance(it, dict):
                        add(it.get("code") or it.get("dtc"), it.get("description") or it.get("desc") or it.get("text"))
            elif isinstance(v, dict):
                add(v.get("code") or v.get("dtc"), v.get("description") or v.get("desc") or v.get("text"))
        return out

    if isinstance(data, list):
        for it in data:
            if isinstance(it, dict):
                add(it.get("code") or it.get("dtc"), it.get("description") or it.get("desc") or it.get("text"))
            elif isinstance(it, str):
                c = norm_code(it)
                if c:
                    rest = it.replace(c, "").strip(" :-\t")
                    if rest:
                        out.append((c, rest, manufacturer, engine_model, ecu_model))
        return out

    return out

def parse_csv_like(path: Path, manufacturer: str, engine_model: str | None, ecu_model: str | None) -> list[tuple[str, str, str, str | None, str | None]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    sample = raw[:4096]
    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    rdr = csv.DictReader(raw.splitlines(), dialect=dialect)
    fieldnames = rdr.fieldnames or []
    fieldnames_l = [f.lower() for f in fieldnames]

    def pick(d: dict, keys: list[str]) -> str | None:
        for k in keys:
            for fk in d.keys():
                if fk and fk.lower() == k:
                    return d.get(fk)
        return None

    out: list[tuple[str, str, str, str | None, str | None]] = []

    for row in rdr:
        code = pick(row, ["code", "dtc", "fault_code"])
        desc = pick(row, ["description", "desc", "text", "label", "meaning"])
        c = norm_code(code or "")

        if c and desc:
            out.append((c, str(desc).strip(), manufacturer, engine_model, ecu_model))
            continue

        if len(fieldnames_l) >= 2:
            k0 = fieldnames[0]
            k1 = fieldnames[1]
            c2 = norm_code((row.get(k0) or "").strip())
            d2 = (row.get(k1) or "").strip()
            if c2 and d2:
                out.append((c2, d2, manufacturer, engine_model, ecu_model))

    return out

def parse_text_lines(path: Path, manufacturer: str, engine_model: str | None, ecu_model: str | None) -> list[tuple[str, str, str, str | None, str | None]]:
    out: list[tuple[str, str, str, str | None, str | None]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        c = norm_code(s)
        if not c:
            continue
        rest = re.sub(rf"\b{re.escape(c)}\b", "", s, count=1).strip(" :-\t;|")
        if rest:
            out.append((c, rest, manufacturer, engine_model, ecu_model))
    return out

def iter_candidate_files(data_dir: Path) -> list[Path]:
    exts = {".json", ".csv", ".tsv", ".txt", ".dat"}
    files: list[Path] = []
    for p in data_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.name.lower() == "desc.ini":
            continue
        if p.suffix.lower() not in exts:
            continue
        name = p.name.lower()
        if "dtc" in name or "obd" in name or "fault" in name or "trouble" in name or "codes" in name:
            files.append(p)
    if files:
        return files

    files = []
    for p in data_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.name.lower() == "desc.ini":
            continue
        if p.suffix.lower() in exts:
            files.append(p)
    return files

def build_tree(rows: list[tuple[str, str, str, str | None, str | None]]):
    tree: dict[str, dict[str, dict[str, dict[str, str]]]] = {}
    n = 0
    for code, desc, manufacturer, engine_model, ecu_model in rows:
        m = node_name(manufacturer)
        e = node_name(engine_model)
        u = node_name(ecu_model)

        if m not in tree:
            tree[m] = {}
        if e not in tree[m]:
            tree[m][e] = {}
        if u not in tree[m][e]:
            tree[m][e][u] = {}

        if code not in tree[m][e][u]:
            tree[m][e][u][code] = desc
            n += 1
    return tree, n

def ensure_outdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_single_json(out_path: Path, tree) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(tree, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_split_json(out_dir: Path, tree) -> None:
    ensure_outdir(out_dir)
    (out_dir / "index.json").write_text(json.dumps({"manufacturers": sorted(tree.keys())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for m, engines in tree.items():
        m_dir = out_dir / m
        ensure_outdir(m_dir)
        (m_dir / "index.json").write_text(json.dumps({"manufacturer": None if m == NULL_NODE else m, "engines": sorted(engines.keys())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        for e, ecus in engines.items():
            e_dir = m_dir / e
            ensure_outdir(e_dir)
            (e_dir / "index.json").write_text(json.dumps({"manufacturer": None if m == NULL_NODE else m, "engine_model": None if e == NULL_NODE else e, "ecus": sorted(ecus.keys())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            for u, codes in ecus.items():
                u_dir = e_dir / u
                ensure_outdir(u_dir)
                (u_dir / "dtc.json").write_text(
                    json.dumps(
                        {
                            "manufacturer": None if m == NULL_NODE else m,
                            "engine_model": None if e == NULL_NODE else e,
                            "ecu_model": None if u == NULL_NODE else u,
                            "dtc": codes,
                        },
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )

def main() -> int:
    ap = argparse.ArgumentParser(description="Compile Autodiag DTC directory layout into JSON.")
    ap.add_argument("--repo", default=".", help="Path to cloned autodiag2/database repo (default: .)")
    ap.add_argument("--data", default=None, help="Data directory inside repo (default: <repo>/data)")
    ap.add_argument("--out", default="dtc.json", help="Single JSON output path (default: dtc.json)")
    ap.add_argument("--split-dir", default=None, help="If set, also write a directory hierarchy with JSON files")
    ap.add_argument("--only", default=None, help="Regex filter applied to relative file path")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    data_dir = Path(args.data).resolve() if args.data else (repo / "data")
    if not data_dir.exists():
        raise SystemExit(f"data directory not found: {data_dir}")

    only_re = re.compile(args.only) if args.only else None
    candidates = iter_candidate_files(data_dir)

    desc_cache: dict[Path, dict[str, str | None]] = {}

    total_files = 0
    rows: list[tuple[str, str, str, str | None, str | None]] = []

    for p in candidates:
        rel = str(p.relative_to(repo)) if repo in p.parents else str(p)
        if only_re and not only_re.search(rel):
            continue

        if p.parent not in desc_cache:
            desc_cache[p.parent] = load_desc_ini(p.parent / "desc.ini")

        meta = desc_cache[p.parent]
        manufacturer = (meta.get("manufacturer") or DEFAULT_MANUFACTURER) or DEFAULT_MANUFACTURER
        engine_model = meta.get("engine") or None
        ecu_model = meta.get("ecu") or None
        if ecu_model and ecu_model.lower().endswith(".ini"):
            ecu_model = ecu_model[:-4]

        total_files += 1

        try:
            suf = p.suffix.lower()
            if suf == ".json":
                rows.extend(parse_json(p, manufacturer, engine_model, ecu_model))
            elif suf in {".csv", ".tsv"}:
                rows.extend(parse_csv_like(p, manufacturer, engine_model, ecu_model))
            else:
                rows.extend(parse_text_lines(p, manufacturer, engine_model, ecu_model))
        except Exception:
            continue

    tree, n = build_tree(rows)

    out_path = Path(args.out).resolve()
    write_single_json(out_path, tree)

    if args.split_dir:
        write_split_json(Path(args.split_dir).resolve(), tree)

    print(f"scanned_files={total_files}")
    print(f"exported_rows={n}")
    print(f"json={out_path}")
    if args.split_dir:
        print(f"split_dir={Path(args.split_dir).resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

