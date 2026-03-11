import sqlite3
import yaml
import pathlib
from pathlib import Path
import json
import datetime


class Converter():

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
                type text default 'PCM',
                foreign key(manufacturer_id) references ad_manufacturer(id)
            );

            create table if not exists ad_engine(
                id integer primary key autoincrement,
                manufacturer_id integer,
                model text,
                foreign key(manufacturer_id) references ad_manufacturer(id)
            );

            create table if not exists ad_vehicle(
                id integer primary key autoincrement,
                manufacturer_id integer,
                model text,
                years text,
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

            -- Normalized DTC attributes
            create table if not exists ad_dtc_system(id integer primary key autoincrement, name text unique);
            create table if not exists ad_dtc_subsystem(id integer primary key autoincrement, name text unique);
            create table if not exists ad_dtc_category(id integer primary key autoincrement, name text unique);
            create table if not exists ad_dtc_severity(id integer primary key autoincrement, name text unique);

            create table if not exists ad_dtc(
                id integer primary key autoincrement,
                code text,
                definition text,
                description text,
                mil boolean,
                created text,
                updated text,
                detection_condition text,
                causes text,
                repairs text,
                evidence text
            );

            -- Links DTCs to standards and protocols
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

            -- Links DTCs to ECUs and Engines (0..N)
            create table if not exists ad_dtc_ecu_link(
                dtc_id integer,
                ecu_id integer,
                foreign key(dtc_id) references ad_dtc(id),
                foreign key(ecu_id) references ad_ecu(id)
            );

            create table if not exists ad_dtc_engine_link(
                dtc_id integer,
                engine_id integer,
                foreign key(dtc_id) references ad_dtc(id),
                foreign key(engine_id) references ad_engine(id)
            );

            -- Related codes as separate table
            create table if not exists ad_dtc_related(
                dtc_id integer,
                related_dtc_id integer,
                foreign key(dtc_id) references ad_dtc(id),
                foreign key(related_dtc_id) references ad_dtc(id)
            );

            -- Many-to-many for system, subsystem, category, severity
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
        delete from ad_dtc;
        delete from ad_ecu;
        delete from ad_engine;
        delete from ad_vehicle;
        delete from ad_manufacturer;
        delete from ad_dtc_standard;
        delete from ad_diag_protocol;
        delete from ad_dtc_ecu_link;
        delete from ad_dtc_engine_link;
        delete from ad_dtc_related;
        delete from ad_dtc_system_link;
        delete from ad_dtc_subsystem_link;
        delete from ad_dtc_category_link;
        delete from ad_dtc_severity_link;
        """)

    def _get_or_insert(self, conn, table, field, value):

        cur = conn.cursor()
        cur.execute(f"select id from {table} where {field}=?", (value,))
        r = cur.fetchone()
        if r:
            return r[0]

        cur.execute(f"insert into {table}({field}) values(?)", (value,))
        return cur.lastrowid

    def to_sqlite(self, progress_callback) -> bool:

        if self.plain_text_db is None or self.sqlite_db is None:
            return False

        conn = self._connect()
        self._create_schema(conn)
        self._clear_tables(conn)

        ecu_root = self.plain_text_db / "ecu"
        if ecu_root.exists():
            for y in ecu_root.rglob("*.yml"):
                with open(y) as f:
                    d = yaml.safe_load(f)

                scope = d.get("scope", {})
                manufacturer = scope.get("manufacturer")
                model = d.get("model")
                if not manufacturer:
                    continue

                mid = self._get_or_insert(conn, "ad_manufacturer", "name", manufacturer)
                cur = conn.cursor()
                cur.execute(
                    "insert into ad_ecu(manufacturer_id, model, type) values(?,?,?)",
                    (mid, model, d.get("type", "PCM"))
                )
                ecu_id = cur.lastrowid

        engine_root = self.plain_text_db / "engine"
        if engine_root.exists():
            for y in engine_root.rglob("*.yml"):
                with open(y) as f:
                    d = yaml.safe_load(f)

                scope = d.get("scope", {})
                manufacturer = scope.get("manufacturer")
                model = d.get("model")
                if not manufacturer:
                    continue

                mid = self._get_or_insert(conn, "ad_manufacturer", "name", manufacturer)
                cur = conn.cursor()
                cur.execute(
                    "insert into ad_engine(manufacturer_id, model) values(?,?)",
                    (mid, model)
                )
                engine_id = cur.lastrowid

        dtcs = list(pathlib.Path(self.plain_text_db / "vehicle").rglob("*.yml"))
        dtcs_len = len(dtcs)
        dtc_count = 0
        progress_callback(dtc_count, dtcs_len)

        for dtc_def in dtcs:
            dtc_count += 1
            progress_callback(dtc_count, dtcs_len)

            with open(dtc_def) as f:
                d = yaml.safe_load(f)

            scope = d.get("scope", {})
            manufacturers = scope.get("manufacturer", [])
            protocols = scope.get("protocol", [])
            standards = scope.get("standard", [])
            ecus = scope.get("ecu", [])
            engines = scope.get("engine", [])

            if isinstance(manufacturers, str):
                manufacturers = [manufacturers]
            if isinstance(protocols, str):
                protocols = [protocols]
            if isinstance(standards, str):
                standards = [standards]
            if isinstance(ecus, int):
                ecus = [ecus]
            if isinstance(engines, int):
                engines = [engines]

            for m in manufacturers:
                self._get_or_insert(conn, "ad_manufacturer", "name", m)

            cur = conn.cursor()
            created = d.get("created") or datetime.datetime.now().isoformat()
            updated = d.get("updated") or created

            cur.execute(
                "insert into ad_dtc(code, definition, description, mil, created, updated, detection_condition, causes, repairs, evidence) "
                "values(?,?,?,?,?,?,?,?,?,?)",
                (
                    d.get("code"),
                    d.get("definition"),
                    d.get("description"),
                    d.get("mil"),
                    created,
                    updated,
                    json.dumps(d.get("detection_condition", [])),
                    json.dumps(d.get("causes", [])),
                    json.dumps(d.get("repairs", [])),
                    json.dumps(d.get("evidence", {})),
                )
            )
            dtc_id = cur.lastrowid

            # Related codes
            for r in d.get("related_code", []):
                cur.execute(
                    "insert into ad_dtc_related(dtc_id, related_dtc_id) values(?, (select id from ad_dtc where code=?))",
                    (dtc_id, r)
                )

            # Standards & protocols
            for s in standards:
                sid = self._get_or_insert(conn, "ad_dtc_standard", "name", s)
                conn.execute("insert into ad_dtc_standard_link values(?,?)", (dtc_id, sid))

            for p in protocols:
                pid = self._get_or_insert(conn, "ad_diag_protocol", "name", p)
                conn.execute("insert into ad_dtc_protocol_link values(?,?)", (dtc_id, pid))

            # ECUs & Engines
            for e in ecus:
                conn.execute("insert into ad_dtc_ecu_link(dtc_id, ecu_id) values(?,?)", (dtc_id, e))
            for en in engines:
                conn.execute("insert into ad_dtc_engine_link(dtc_id, engine_id) values(?,?)", (dtc_id, en))

            # System, Subsystem, Category, Severity links
            for sys_name in d.get("system", []):
                sys_id = self._get_or_insert(conn, "ad_dtc_system", "name", sys_name)
                conn.execute("insert into ad_dtc_system_link values(?,?)", (dtc_id, sys_id))
            for sub_name in d.get("subsystem", []):
                sub_id = self._get_or_insert(conn, "ad_dtc_subsystem", "name", sub_name)
                conn.execute("insert into ad_dtc_subsystem_link values(?,?)", (dtc_id, sub_id))
            for cat_name in d.get("category", []):
                cat_id = self._get_or_insert(conn, "ad_dtc_category", "name", cat_name)
                conn.execute("insert into ad_dtc_category_link values(?,?)", (dtc_id, cat_id))
            for sev_name in d.get("severity", []):
                sev_id = self._get_or_insert(conn, "ad_dtc_severity", "name", sev_name)
                conn.execute("insert into ad_dtc_severity_link values(?,?)", (dtc_id, sev_id))

        conn.commit()
        conn.close()
        return True