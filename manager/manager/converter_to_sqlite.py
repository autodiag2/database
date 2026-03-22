#!python3
import sys
import sqlite3
import yaml
from pathlib import Path
import json
import datetime
from tqdm import tqdm
from manager.vpic_sqlite_loader import VpicToSqliteLoader


class ConverterToSqlite():

    def __init__(self, plain_text_db: Path = None, sqlite_db: Path = None):
        self.plain_text_db = Path(plain_text_db) if plain_text_db else None
        self.sqlite_db = Path(sqlite_db) if sqlite_db else None

    def _connect(self):
        conn = sqlite3.connect(self.sqlite_db)
        conn.execute("pragma foreign_keys = on")
        return conn

    def _create_schema(self, conn):
        conn.executescript("""
        create table if not exists ad_manufacturer(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ad_ecu(
            id integer primary key autoincrement,
            manufacturer_id integer,
            model text,
            type text default 'ECM',
            foreign key(manufacturer_id) references ad_manufacturer(id)
        );

        create table if not exists ad_dtc_standard(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ad_diag_protocol(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ad_dtc_system(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ad_dtc_subsystem(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ad_dtc_category(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ad_dtc_severity(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ad_dtc(
            id integer primary key autoincrement,
            ecu_id integer not null,
            code text,
            definition text,
            description text,
            mil boolean,
            created text,
            updated text,
            detection_condition text,
            causes text,
            repairs text,
            evidence text,
            foreign key(ecu_id) references ad_ecu(id)
        );

        create unique index if not exists ad_dtc_ecu_code_uq
        on ad_dtc(ecu_id, code);

        create table if not exists ad_dtc_standard_link(
            dtc_id integer,
            standard_id integer,
            foreign key(dtc_id) references ad_dtc(id),
            foreign key(standard_id) references ad_dtc_standard(id)
        );

        create table if not exists ad_dtc_protocol_link(
            dtc_id integer,
            protocol_id integer,
            foreign key(dtc_id) references ad_dtc(id),
            foreign key(protocol_id) references ad_diag_protocol(id)
        );

        create table if not exists ad_dtc_related(
            dtc_id integer,
            related_dtc_id integer,
            foreign key(dtc_id) references ad_dtc(id),
            foreign key(related_dtc_id) references ad_dtc(id)
        );

        create table if not exists ad_dtc_system_link(
            dtc_id integer,
            system_id integer,
            foreign key(dtc_id) references ad_dtc(id),
            foreign key(system_id) references ad_dtc_system(id)
        );

        create table if not exists ad_dtc_subsystem_link(
            dtc_id integer,
            subsystem_id integer,
            foreign key(dtc_id) references ad_dtc(id),
            foreign key(subsystem_id) references ad_dtc_subsystem(id)
        );

        create table if not exists ad_dtc_category_link(
            dtc_id integer,
            category_id integer,
            foreign key(dtc_id) references ad_dtc(id),
            foreign key(category_id) references ad_dtc_category(id)
        );

        create table if not exists ad_dtc_severity_link(
            dtc_id integer,
            severity_id integer,
            foreign key(dtc_id) references ad_dtc(id),
            foreign key(severity_id) references ad_dtc_severity(id)
        );
        """)

    def _clear_tables(self, conn):
        conn.executescript("""
        delete from ad_dtc_protocol_link;
        delete from ad_dtc_standard_link;
        delete from ad_dtc_related;
        delete from ad_dtc_system_link;
        delete from ad_dtc_subsystem_link;
        delete from ad_dtc_category_link;
        delete from ad_dtc_severity_link;
        delete from ad_dtc;
        delete from ad_ecu;
        delete from ad_manufacturer;
        delete from ad_dtc_standard;
        delete from ad_diag_protocol;
        delete from ad_dtc_system;
        delete from ad_dtc_subsystem;
        delete from ad_dtc_category;
        delete from ad_dtc_severity;
        """)

    def _read_yaml(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _get_or_insert(self, conn, table, field, value):
        if value is None or value == "":
            return None
        cur = conn.cursor()
        cur.execute(f"select id from {table} where {field}=?", (value,))
        r = cur.fetchone()
        if r:
            return r[0]
        cur.execute(f"insert into {table}({field}) values(?)", (value,))
        return cur.lastrowid

    def _ensure_list(self, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [x for x in v if x is not None and x != ""]
        return [v]

    def _get_or_insert_ecu(self, conn, manufacturer, model, ecu_type="ECM"):
        if manufacturer is None or manufacturer == "" or model is None or model == "":
            return None
        mid = self._get_or_insert(conn, "ad_manufacturer", "name", manufacturer)
        cur = conn.cursor()
        cur.execute(
            "select id from ad_ecu where manufacturer_id=? and model=? and type=?",
            (mid, model, ecu_type)
        )
        r = cur.fetchone()
        if r:
            return r[0]
        cur.execute(
            "insert into ad_ecu(manufacturer_id, model, type) values(?,?,?)",
            (mid, model, ecu_type)
        )
        return cur.lastrowid

    def _json_dump(self, value, default):
        if value is None:
            value = default
        return json.dumps(value, ensure_ascii=False)

    def _iter_ecu_entries(self):
        ecu_root = self.plain_text_db / "ecu"
        if not ecu_root.exists():
            return

        for manufacturer_dir in sorted(p for p in ecu_root.iterdir() if p.is_dir()):
            manufacturer_def = self._read_yaml(manufacturer_dir / "def.yml")
            manufacturer = manufacturer_def.get("manufacturer") or manufacturer_dir.name

            manufacturer_codes_dir = manufacturer_dir / "codes"
            if manufacturer_codes_dir.exists() and manufacturer_codes_dir.is_dir():
                for y in sorted(manufacturer_codes_dir.glob("*.yml")):
                    yield {
                        "path": y,
                        "manufacturer": manufacturer,
                        "ecu_model": None,
                        "ecu_type": "ECM",
                    }

            for entry_dir in sorted(p for p in manufacturer_dir.iterdir() if p.is_dir()):
                if entry_dir.name == "codes":
                    continue

                entry_def_path = entry_dir / "def.yml"
                if not entry_def_path.exists():
                    continue

                entry_def = self._read_yaml(entry_def_path)
                ecu_model = entry_def.get("model")
                ecu_type = entry_def.get("type", "ECM")

                if ecu_model:
                    yield {
                        "path": entry_def_path,
                        "manufacturer": manufacturer,
                        "ecu_model": ecu_model,
                        "ecu_type": ecu_type,
                        "is_def": True,
                    }

                codes_dir = entry_dir / "codes"
                if codes_dir.exists() and codes_dir.is_dir():
                    for y in sorted(codes_dir.glob("*.yml")):
                        yield {
                            "path": y,
                            "manufacturer": manufacturer,
                            "ecu_model": ecu_model,
                            "ecu_type": ecu_type,
                            "is_def": False,
                        }

    def _load_ecus(self, conn):
        seen = set()

        for entry in self._iter_ecu_entries():
            manufacturer = entry["manufacturer"]
            ecu_model = entry["ecu_model"]
            ecu_type = entry["ecu_type"]

            if ecu_model is None or ecu_model == "":
                continue

            key = (manufacturer, ecu_model, ecu_type)
            if key in seen:
                continue
            seen.add(key)

            self._get_or_insert_ecu(conn, manufacturer, ecu_model, ecu_type)

    def _insert_taxonomy_links(self, conn, dtc_id, d):
        for sys_name in self._ensure_list(d.get("system")):
            sid = self._get_or_insert(conn, "ad_dtc_system", "name", sys_name)
            if sid is not None:
                conn.execute(
                    "insert into ad_dtc_system_link(dtc_id, system_id) values(?,?)",
                    (dtc_id, sid)
                )

        for sub_name in self._ensure_list(d.get("subsystem")):
            sid = self._get_or_insert(conn, "ad_dtc_subsystem", "name", sub_name)
            if sid is not None:
                conn.execute(
                    "insert into ad_dtc_subsystem_link(dtc_id, subsystem_id) values(?,?)",
                    (dtc_id, sid)
                )

        for cat_name in self._ensure_list(d.get("category")):
            cid = self._get_or_insert(conn, "ad_dtc_category", "name", cat_name)
            if cid is not None:
                conn.execute(
                    "insert into ad_dtc_category_link(dtc_id, category_id) values(?,?)",
                    (dtc_id, cid)
                )

        for sev_name in self._ensure_list(d.get("severity")):
            sid = self._get_or_insert(conn, "ad_dtc_severity", "name", sev_name)
            if sid is not None:
                conn.execute(
                    "insert into ad_dtc_severity_link(dtc_id, severity_id) values(?,?)",
                    (dtc_id, sid)
                )

        for proto_name in self._ensure_list(d.get("protocol")):
            pid = self._get_or_insert(conn, "ad_diag_protocol", "name", proto_name)
            if pid is not None:
                conn.execute(
                    "insert into ad_dtc_protocol_link(dtc_id, protocol_id) values(?,?)",
                    (dtc_id, pid)
                )

        for std_name in self._ensure_list(d.get("standard")):
            sid = self._get_or_insert(conn, "ad_dtc_standard", "name", std_name)
            if sid is not None:
                conn.execute(
                    "insert into ad_dtc_standard_link(dtc_id, standard_id) values(?,?)",
                    (dtc_id, sid)
                )

    def _insert_related_codes(self, conn, dtc_id, related_codes, ecu_id):
        for code in self._ensure_list(related_codes):
            conn.execute("""
                insert into ad_dtc_related(dtc_id, related_dtc_id)
                select ?, id
                from ad_dtc
                where code=?
                  and ecu_id=?
            """, (dtc_id, code, ecu_id))

    def to_sqlite(self, progress_callback) -> bool:
        if self.plain_text_db is None or self.sqlite_db is None:
            return False

        conn = self._connect()
        self._create_schema(conn)
        self._clear_tables(conn)
        self._load_ecus(conn)

        dtc_entries = [
            entry for entry in self._iter_ecu_entries()
            if entry.get("is_def") is False
        ]

        total = len(dtc_entries)
        count = 0
        progress_callback(count, total)

        cur = conn.cursor()

        for entry in dtc_entries:
            count += 1
            progress_callback(count, total)

            y = entry["path"]
            manufacturer = entry["manufacturer"]
            ecu_model = entry["ecu_model"]
            ecu_type = entry["ecu_type"]

            d = self._read_yaml(y)

            ecu_id = None
            if ecu_model:
                ecu_id = self._get_or_insert_ecu(conn, manufacturer, ecu_model, ecu_type)
            if ecu_id is None:
                continue

            created = d.get("created") or datetime.datetime.now().isoformat()
            updated = d.get("updated") or created

            cur.execute("""
                insert into ad_dtc(
                    ecu_id,
                    code,
                    definition,
                    description,
                    mil,
                    created,
                    updated,
                    detection_condition,
                    causes,
                    repairs,
                    evidence
                ) values(?,?,?,?,?,?,?,?,?,?,?)
            """, (
                ecu_id,
                d.get("code") or y.stem,
                d.get("definition"),
                d.get("description"),
                d.get("mil"),
                created,
                updated,
                self._json_dump(d.get("detection_condition"), []),
                self._json_dump(d.get("causes"), []),
                self._json_dump(d.get("repairs"), []),
                self._json_dump(d.get("evidence"), {}),
            ))

            dtc_id = cur.lastrowid

            self._insert_related_codes(conn, dtc_id, d.get("related_code"), ecu_id)
            self._insert_taxonomy_links(conn, dtc_id, d)

        conn.commit()
        conn.close()
        return True


def main():
    base = Path(__file__).resolve().parent.parent.parent

    src = base / "data-src"
    dst = base / "data" / "ad_database.sqlite"

    if 1 < len(sys.argv):
        src = Path(sys.argv[1])
    if 2 < len(sys.argv):
        dst = Path(sys.argv[2])

    converter = ConverterToSqlite(sqlite_db=dst, plain_text_db=src)
    bar = {"pbar": None, "total": 0}

    def progress_hook(current, total):
        if bar["pbar"] is None:
            bar["total"] = total
            bar["pbar"] = tqdm(total=total, unit="item")
        delta = current - bar["pbar"].n
        if 0 < delta:
            bar["pbar"].update(delta)

    ok = converter.to_sqlite(progress_callback=progress_hook)

    if bar["pbar"] is not None:
        bar["pbar"].close()

    if ok:
        print("Success")
    else:
        print("Export failed")

    loader = VpicToSqliteLoader(
        sqlite_path=str(dst),
        pg_host="localhost",
        pg_port="5432",
        pg_user="jean",
        pg_password="",
        pg_dbname="vpic_lite",
        pg_schema="vpic",
    )

    bar = {"pbar": None, "total": 0}

    ok = loader.load(progress_callback=progress_hook)

    if bar["pbar"] is not None:
        bar["pbar"].close()

    if ok:
        print("vpic loaded")
    else:
        print("error while loading vpic")


if __name__ == "__main__":
    main()