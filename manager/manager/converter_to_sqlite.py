#!python3
import sys
import sqlite3
import yaml
from pathlib import Path
import json
import datetime
from tqdm import tqdm
from manager.vpic_sqlite_loader import VpicToSqliteLoader
from manager.tab.import_vehicle import slug

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
                name text unique not null
            );

            create table if not exists ad_mcu(
                id integer primary key autoincrement,
                manufacturer_id integer not null,
                model text not null,
                created text,
                updated text,
                foreign key(manufacturer_id) references ad_manufacturer(id)
            );

            create unique index if not exists ad_mcu_uq
            on ad_mcu(manufacturer_id, model);

            create table if not exists ad_engine(
                id integer primary key autoincrement,
                manufacturer_id integer not null,
                code text,
                fuel text,
                created text,
                updated text,
                foreign key(manufacturer_id) references ad_manufacturer(id)
            );

            create unique index if not exists ad_engine_uq
            on ad_engine(manufacturer_id, code);
                           
            create table if not exists ad_engine_name(
                engine_id integer not null,
                name text not null,
                primary key(engine_id, name),
                foreign key(engine_id) references ad_engine(id)
            );

            create table if not exists ad_ecu(
                id integer primary key autoincrement,
                manufacturer_id integer not null,
                mcu_id integer,
                model text not null,
                type text default 'ECM',
                created text,
                updated text,
                foreign key(manufacturer_id) references ad_manufacturer(id),
                foreign key(mcu_id) references ad_mcu(id)
            );

            create unique index if not exists ad_ecu_uq
            on ad_ecu(manufacturer_id, model);

            create table if not exists ad_vehicle(
                id integer primary key autoincrement,
                manufacturer_id integer not null,
                model text not null,
                type text,
                created text,
                updated text,
                foreign key(manufacturer_id) references ad_manufacturer(id)
            );

            create unique index if not exists ad_vehicle_uq
            on ad_vehicle(manufacturer_id, model);

            create table if not exists ad_vehicle_version(
                id integer primary key autoincrement,
                vehicle_id integer not null,
                version text,
                year text,
                engine_id integer,
                ecu_id integer,
                power_ps integer,
                power_kw real,
                created text,
                updated text,
                foreign key(vehicle_id) references ad_vehicle(id),
                foreign key(engine_id) references ad_engine(id),
                foreign key(ecu_id) references ad_ecu(id)
            );

            create unique index if not exists ad_vehicle_version_uq
            on ad_vehicle_version(vehicle_id, version);

            create table if not exists ad_vehicle_version_alt_ecu(
                vehicle_version_id integer not null,
                ecu_id integer not null,
                primary key(vehicle_version_id, ecu_id),
                foreign key(vehicle_version_id) references ad_vehicle_version(id),
                foreign key(ecu_id) references ad_ecu(id)
            );

            create table if not exists ad_evidence(
                id integer primary key autoincrement,
                text text unique not null
            );

            create table if not exists ad_manufacturer_evidence(
                manufacturer_id integer not null,
                evidence_id integer not null,
                primary key(manufacturer_id, evidence_id),
                foreign key(manufacturer_id) references ad_manufacturer(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

            create table if not exists ad_vehicle_evidence(
                vehicle_id integer not null,
                evidence_id integer not null,
                primary key(vehicle_id, evidence_id),
                foreign key(vehicle_id) references ad_vehicle(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

            create table if not exists ad_vehicle_version_evidence(
                vehicle_version_id integer not null,
                evidence_id integer not null,
                primary key(vehicle_version_id, evidence_id),
                foreign key(vehicle_version_id) references ad_vehicle_version(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

            create table if not exists ad_engine_evidence(
                engine_id integer not null,
                evidence_id integer not null,
                primary key(engine_id, evidence_id),
                foreign key(engine_id) references ad_engine(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

            create table if not exists ad_ecu_evidence(
                ecu_id integer not null,
                evidence_id integer not null,
                primary key(ecu_id, evidence_id),
                foreign key(ecu_id) references ad_ecu(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

            create table if not exists ad_mcu_evidence(
                mcu_id integer not null,
                evidence_id integer not null,
                primary key(mcu_id, evidence_id),
                foreign key(mcu_id) references ad_mcu(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

            create table if not exists ad_conflict(
                id integer primary key autoincrement,
                entity_type text not null,
                entity_id integer not null,
                field text not null,
                created text
            );

            create table if not exists ad_conflict_value(
                id integer primary key autoincrement,
                conflict_id integer not null,

                value_text text,

                ref_entity_type text,
                ref_entity_id integer,

                foreign key(conflict_id) references ad_conflict(id),

                check(
                    (value_text is not null and ref_entity_type is null and ref_entity_id is null)
                    or
                    (value_text is null and ref_entity_type is not null and ref_entity_id is not null)
                )
            );

            create table if not exists ad_conflict_value_evidence(
                conflict_value_id integer not null,
                evidence_id integer not null,
                primary key(conflict_value_id, evidence_id),
                foreign key(conflict_value_id) references ad_conflict_value(id),
                foreign key(evidence_id) references ad_evidence(id)
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
                foreign key(ecu_id) references ad_ecu(id)
            );
                           
            create unique index if not exists ad_dtc_ecu_code_uq
            on ad_dtc(ecu_id, code);
                           
            create table if not exists ad_dtc_evidence(
                dtc_id integer not null,
                evidence_id integer not null,
                primary key(dtc_id, evidence_id),
                foreign key(dtc_id) references ad_dtc(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

            create table if not exists ad_dtc_evidence(
                dtc_id integer not null,
                evidence_id integer not null,
                primary key(dtc_id, evidence_id),
                foreign key(dtc_id) references ad_dtc(id),
                foreign key(evidence_id) references ad_evidence(id)
            );

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
        delete from ad_conflict_value_evidence;
        delete from ad_conflict_value;
        delete from ad_conflict;

        delete from ad_dtc_standard_link;
        delete from ad_dtc_protocol_link;
        delete from ad_dtc_related;
        delete from ad_dtc_system_link;
        delete from ad_dtc_subsystem_link;
        delete from ad_dtc_category_link;
        delete from ad_dtc_severity_link;

        delete from ad_dtc_evidence;
        delete from ad_vehicle_version_alt_ecu;

        delete from ad_manufacturer_evidence;
        delete from ad_vehicle_evidence;
        delete from ad_vehicle_version_evidence;
        delete from ad_engine_evidence;
        delete from ad_engine_name;
        delete from ad_ecu_evidence;
        delete from ad_mcu_evidence;

        delete from ad_dtc;
        delete from ad_vehicle_version;
        delete from ad_vehicle;
        delete from ad_ecu;
        delete from ad_engine;
        delete from ad_mcu;

        delete from ad_dtc_standard;
        delete from ad_diag_protocol;
        delete from ad_dtc_system;
        delete from ad_dtc_subsystem;
        delete from ad_dtc_category;
        delete from ad_dtc_severity;

        delete from ad_manufacturer;
        delete from ad_evidence;
        """)

    def _read_yaml(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _get_or_insert(self, conn, table, field, value, ignore_case=False):
        if value is None or value == "":
            return None

        cur = conn.cursor()

        if ignore_case:
            cur.execute(
                f"select id from {table} where lower({field}) = lower(?)",
                (value,),
            )
        else:
            cur.execute(
                f"select id from {table} where {field} = ?",
                (value,),
            )

        r = cur.fetchone()
        if r:
            return r[0]

        cur.execute(
            f"insert into {table}({field}) values(?)",
            (value,),
        )

        return cur.lastrowid

    def _ensure_list(self, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [x for x in v if x is not None and x != ""]
        return [v]

    def _get_or_insert_evidence(self, conn, text):
        if not text:
            return None

        cur = conn.cursor()

        cur.execute(
            "select id from ad_evidence where text=?",
            (text,)
        )

        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute(
            "insert into ad_evidence(text) values(?)",
            (text,)
        )

        return cur.lastrowid
    
    def _link_evidence(self, conn, table, entity_field, entity_id, evidence):
        if entity_id is None:
            return

        for text in self._ensure_list(evidence):
            evidence_id = self._get_or_insert_evidence(conn, text)

            conn.execute(
                f"""
                insert or ignore into {table}
                ({entity_field}, evidence_id)
                values(?, ?)
                """,
                (entity_id, evidence_id),
            )

    def _get_or_insert_mcu(
        self,
        conn,
        manufacturer,
        model,
        created=None,
        updated=None,
        evidence=None,
    ):
        if not manufacturer or not model:
            return None

        manufacturer_id = self._get_or_insert(
            conn,
            "ad_manufacturer",
            "name",
            manufacturer,
            True
        )

        cur = conn.cursor()

        cur.execute("""
            select id, created, updated
            from ad_mcu
            where manufacturer_id=?
            and model=?
        """, (
            manufacturer_id,
            slug(model),
        ))

        row = cur.fetchone()

        if row:
            mcu_id = row[0]

            if not created:
                created = row[1]
            if not updated:
                updated = row[2]

            cur.execute("""
                update ad_mcu
                set created=coalesce(created, ?),
                    updated=?
                where id=?
            """, (
                created,
                updated,
                mcu_id,
            ))

        else:
            cur.execute("""
                insert into ad_mcu(
                    manufacturer_id,
                    model,
                    created,
                    updated
                )
                values(?,?,?,?)
            """, (
                manufacturer_id,
                slug(model),
                created,
                updated,
            ))

            mcu_id = cur.lastrowid

        self._link_evidence(
            conn,
            "ad_mcu_evidence",
            "mcu_id",
            mcu_id,
            evidence,
        )

        return mcu_id

    def _get_or_insert_ecu(
        self,
        conn,
        manufacturer,
        model,
        created=None,
        updated=None,
        ecu_type="ECM",
        mcu_ref: int = None,
        evidence=None,
        codes_path=None
    ):
        if not manufacturer or not model:
            return None

        manufacturer_id = self._get_or_insert(
            conn,
            "ad_manufacturer",
            "name",
            manufacturer,
            True
        )

        cur = conn.cursor()

        cur.execute("""
            select id
            from ad_ecu
            where manufacturer_id=?
            and model=?
        """, (
            manufacturer_id,
            model,
        ))

        row = cur.fetchone()

        if row:
            ecu_id = row[0]

            cur.execute("""
                update ad_ecu
                set type=?,
                    mcu_id=coalesce(mcu_id, ?),
                    created=coalesce(created, ?),
                    updated=?
                where id=?
            """, (
                ecu_type,
                mcu_ref,
                created,
                updated,
                ecu_id,
            ))
        else:
            cur.execute("""
                insert into ad_ecu(
                    manufacturer_id,
                    mcu_id,
                    model,
                    type,
                    created,
                    updated
                )
                values(?,?,?,?,?,?)
            """, (
                manufacturer_id,
                mcu_ref,
                model,
                ecu_type,
                created,
                updated,
            ))

            ecu_id = cur.lastrowid

        if evidence:
            if isinstance(evidence, str):
                evidence = [evidence]
            assert type(evidence) == type([])
            for ev in evidence:
                self._link_evidence(
                    conn,
                    "ad_ecu_evidence",
                    "ecu_id",
                    ecu_id,
                    ev,
                )

        if codes_path.exists():
            for y in sorted(codes_path.glob("*.yml")):
                file = self._read_yaml(y)

                created = file.get("created") or datetime.datetime.now().isoformat()
                updated = file.get("updated") or created

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
                        repairs
                    ) values(?,?,?,?,?,?,?,?,?,?)
                """, (
                    ecu_id,
                    file.get("code"),
                    file.get("definition"),
                    file.get("description"),
                    file.get("mil"),
                    created,
                    updated,
                    self._json_dump(file.get("detection_condition"), []),
                    self._json_dump(file.get("causes"), []),
                    self._json_dump(file.get("repairs"), [])
                ))

                dtc_id = cur.lastrowid

                for evidence in (file.get("evidence", []) or []):
                    self._link_evidence(conn, "ad_dtc_evidence", "dtc_id", dtc_id, evidence)

                self._insert_related_codes(conn, dtc_id, file.get("related_code"), ecu_id)
                self._insert_taxonomy_links(conn, dtc_id, file)

        return ecu_id

    def _iter_mcu_entries(self):
        mcu_root = self.plain_text_db / "mcu"
        if not mcu_root.exists():
            return

        for manufacturer_dir in sorted(p for p in mcu_root.iterdir() if p.is_dir()):

            manufacturer_def = self._read_yaml(manufacturer_dir / "def.yml")
            manufacturer = (
                manufacturer_def.get("manufacturer")
                or manufacturer_dir.name
            )

            for mcu_dir in sorted(p for p in manufacturer_dir.iterdir() if p.is_dir()):

                def_path = mcu_dir / "def.yml"
                if not def_path.exists():
                    continue

                data = self._read_yaml(def_path)

                yield {
                    "manufacturer": manufacturer,
                    "model": data.get("model"),
                    "created": data.get("created"),
                    "updated": data.get("updated"),
                    "evidence": data.get("evidence", []),
                    "conflicts": data.get("conflicts", {}),
                }

    def _load_mcus(self, conn):
        seen = set()

        for entry in self._iter_mcu_entries():

            manufacturer = entry["manufacturer"]
            model = entry["model"]

            if not manufacturer or not model:
                continue

            key = (manufacturer, model)
            if key in seen:
                continue
            seen.add(key)

            mcu_id = self._get_or_insert_mcu(
                conn,
                manufacturer=manufacturer,
                model=model,
                created=entry["created"],
                updated=entry["updated"],
                evidence=entry["evidence"],
            )

            for field, values in entry["conflicts"].items():

                conflict_id = self._insert_conflict(
                    conn,
                    entity_type="mcu",
                    entity_id=mcu_id,
                    field=field,
                    created=entry["updated"] or entry["created"],
                )

                for value in self._ensure_list(values):

                    conflict_value_id = self._insert_conflict_value(
                        conn,
                        conflict_id,
                        field,
                        value,
                    )

                    self._link_conflict_value_evidence(
                        conn,
                        conflict_value_id,
                        value.get("evidence"),
                    )
                    
    def _json_dump(self, value, default):
        if value is None:
            value = default
        return json.dumps(value, ensure_ascii=False)

    def _iter_ecu_entries(self, conn):
        ecu_root = self.plain_text_db / "ecu"
        if not ecu_root.exists():
            return

        for manufacturer_dir in sorted(p for p in ecu_root.iterdir() if p.is_dir()):

            manufacturer_def = self._read_yaml(manufacturer_dir / "def.yml")
            manufacturer = (
                manufacturer_def.get("manufacturer")
                or manufacturer_dir.name
            )

            for ecu_dir in sorted(
                p for p in manufacturer_dir.iterdir()
                if p.is_dir()
            ):

                def_path = ecu_dir / "def.yml"
                if not def_path.exists():
                    continue
                codes_path = ecu_dir / "codes"

                data = self._read_yaml(def_path)

                mcu_ref = None
                mcu = data.get("mcu")
                if mcu:
                    mcu_manufacturer, mcu_model = mcu.split("/", 1)
                    mcu_ref = self._get_or_insert_mcu(
                        conn,
                        mcu_manufacturer,
                        mcu_model,
                    )

                yield {
                    "path": def_path,
                    "codes_path": codes_path,
                    "manufacturer": manufacturer,
                    "ecu_model": data.get("model"),
                    "created": data.get("created"),
                    "updated": data.get("updated"),
                    "ecu_type": data.get("type", "ECM"),
                    "mcu_ref": mcu_ref,
                    "evidence": data.get("evidence", []),
                    "conflicts": data.get("conflicts", {}),
                }

    def _insert_conflict(
        self,
        conn,
        entity_type,
        entity_id,
        field,
        created=None,
    ):
        cur = conn.execute(
            """
            insert into ad_conflict (
                entity_type,
                entity_id,
                field,
                created
            )
            values (?, ?, ?, ?)
            """,
            (
                entity_type,
                entity_id,
                field,
                created,
            ),
        )
        return cur.lastrowid

    def _insert_conflict_value(
        self,
        conn,
        conflict_id,
        field,
        value,
    ):
        if isinstance(value, dict):
            value = value["value"]

        ref_entity_type = None
        ref_entity_id = None
        value_text = value

        if isinstance(value, str) and "/" in value:
            manufacturer, model = value.split("/", 1)

            lookup = {
                "mcu": self._get_or_insert_mcu,
                "ecu": self._get_or_insert_ecu,
                #"engine": self._get_or_insert_engine,
            }

            if field in lookup:
                ref_entity_type = field
                ref_entity_id = lookup[field](conn, manufacturer, model)
                value_text = None

        cur = conn.execute(
            """
            insert into ad_conflict_value (
                conflict_id,
                value_text,
                ref_entity_type,
                ref_entity_id
            )
            values (?, ?, ?, ?)
            """,
            (
                conflict_id,
                value_text,
                ref_entity_type,
                ref_entity_id,
            ),
        )

        return cur.lastrowid

    def _link_conflict_value_evidence(
        self,
        conn,
        conflict_value_id,
        evidence,
    ):
        if not evidence:
            return

        if isinstance(evidence, str):
            evidence = [evidence]

        for text in evidence:
            evidence_id = self._get_or_insert_evidence(
                conn,
                text,
            )

            conn.execute(
                """
                insert or ignore into ad_conflict_value_evidence (
                    conflict_value_id,
                    evidence_id
                )
                values (?, ?)
                """,
                (
                    conflict_value_id,
                    evidence_id,
                ),
            )
            
    def _load_ecus(self, conn):
        seen = set()

        for entry in self._iter_ecu_entries(conn):

            manufacturer = entry["manufacturer"]
            model = entry["ecu_model"]

            if not manufacturer or not model:
                continue

            key = (manufacturer, model)
            if key in seen:
                continue
            seen.add(key)

            ecu_id = self._get_or_insert_ecu(
                conn,
                manufacturer=manufacturer,
                model=model,
                created=entry["created"],
                updated=entry["updated"],
                ecu_type=entry["ecu_type"],
                mcu_ref=entry["mcu_ref"],
                evidence=entry["evidence"],
                codes_path=entry["codes_path"]
            )

            for field, values in entry["conflicts"].items():

                conflict_id = self._insert_conflict(
                    conn,
                    entity_type="ecu",
                    entity_id=ecu_id,
                    field=field,
                    created=entry["updated"] or entry["created"],
                )

                for value in self._ensure_list(values):

                    conflict_value_id = self._insert_conflict_value(
                        conn,
                        conflict_id,
                        field,
                        value,
                    )

                    self._link_conflict_value_evidence(
                        conn,
                        conflict_value_id,
                        value.get("evidence"),
                    )

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

    def log(self, text):
        print(text)

    def to_sqlite(self, progress_callback) -> bool:
        if self.plain_text_db is None or self.sqlite_db is None:
            return False

        Path("output").mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        self._create_schema(conn)
        self._clear_tables(conn)
        self._load_mcus(conn)
        self._load_ecus(conn)
        self.log("Commiting changes ...")
        conn.commit()
        conn.close()
        self.log("Changes commited !")
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