#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

DEFAULT_MANUFACTURER = "generic"

def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;

        CREATE TABLE IF NOT EXISTS dtc (
            id TEXT NOT NULL,
            desc TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            engine_model TEXT,
            ecu_model TEXT,
            PRIMARY KEY(id, manufacturer, engine_model, ecu_model)
        );

        CREATE INDEX IF NOT EXISTS idx_dtc_id ON dtc(id);
        CREATE INDEX IF NOT EXISTS idx_dtc_manufacturer ON dtc(manufacturer);
        CREATE INDEX IF NOT EXISTS idx_dtc_ecu ON dtc(ecu_model);
        CREATE INDEX IF NOT EXISTS idx_dtc_engine ON dtc(engine_model);
        """
    )

def norm_code(s: str) -> str | None:
    if s is None:
        return None
    s = s.strip().upper()
    m = re.fullmatch(r"[PCBU][0-3][0-9A-F]{3}", s)
    if m:
        return s
    m = re.search(r"\b([PCBU][0-3][0-9A-F]{3})\b", s)
    return m.group(1) if m else None

def insert(conn: sqlite3.Connection, rows: list[tuple[str, str, str, str | None, str | None]]) -> int:
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR IGNORE INTO dtc(id, desc, manufacturer, engine_model, ecu_model) VALUES(?,?,?,?,?)",
        rows,
    )
    return cur.rowcount

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

def main() -> int:
    ap = argparse.ArgumentParser(description="Compile Autodiag DTC files into a SQLite database.")
    ap.add_argument("--repo", default=".", help="Path to cloned autodiag2/database repo (default: .)")
    ap.add_argument("--data", default=None, help="Data directory inside repo (default: <repo>/data)")
    ap.add_argument("--out", default="dtc.sqlite", help="Output sqlite file (default: dtc.sqlite)")
    ap.add_argument("--only", default=None, help="Regex filter applied to relative file path")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    data_dir = Path(args.data).resolve() if args.data else (repo / "data")
    if not data_dir.exists():
        raise SystemExit(f"data directory not found: {data_dir}")

    out_db = Path(args.out).resolve()
    conn = sqlite3.connect(str(out_db))
    try:
        ensure_schema(conn)

        only_re = re.compile(args.only) if args.only else None
        candidates = iter_candidate_files(data_dir)

        desc_cache: dict[Path, dict[str, str | None]] = {}

        total_files = 0
        total_rows = 0

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

            rows: list[tuple[str, str, str, str | None, str | None]] = []
            suf = p.suffix.lower()
            try:
                if suf == ".json":
                    rows = parse_json(p, manufacturer, engine_model, ecu_model)
                elif suf in {".csv", ".tsv"}:
                    rows = parse_csv_like(p, manufacturer, engine_model, ecu_model)
                else:
                    rows = parse_text_lines(p, manufacturer, engine_model, ecu_model)
            except Exception:
                continue

            if rows:
                total_rows += insert(conn, rows)

        conn.commit()
        print(f"sqlite={out_db}")
        print(f"scanned_files={total_files}")
        print(f"inserted_rows={total_rows}")
    finally:
        conn.close()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
