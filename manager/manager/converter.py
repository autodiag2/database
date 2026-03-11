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
        create table if not exists manufacturer(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists ecu(
            id integer primary key autoincrement,
            manufacturer_id integer,
            model text,
            type text default 'PCM',
            foreign key(manufacturer_id) references manufacturer(id)
        );

        create table if not exists engine(
            id integer primary key autoincrement,
            manufacturer_id integer,
            model text,
            foreign key(manufacturer_id) references manufacturer(id)
        );

        create table if not exists vehicle(
            id integer primary key autoincrement,
            manufacturer_id integer,
            model text,
            years text,
            foreign key(manufacturer_id) references manufacturer(id)
        );

        create table if not exists dtc_standard(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists diag_protocol(
            id integer primary key autoincrement,
            name text unique
        );

        create table if not exists dtc(
            id integer primary key autoincrement,
            code text,
            system text,
            subsystem text,
            category text,
            definition text,
            description text,
            severity text,
            mil text,
            created text,
            updated text,
            related_code text,
            detection_condition text,
            causes text,
            repairs text,
            evidence text
        );

        create table if not exists dtc_standard_link(
            dtc_id integer,
            standard_id integer,
            foreign key(dtc_id) references dtc(id),
            foreign key(standard_id) references dtc_standard(id)
        );

        create table if not exists dtc_protocol_link(
            dtc_id integer,
            protocol_id integer,
            foreign key(dtc_id) references dtc(id),
            foreign key(protocol_id) references diag_protocol(id)
        );
        """)

    def _clear_tables(self, conn):

        conn.executescript("""
        delete from dtc_protocol_link;
        delete from dtc_standard_link;
        delete from dtc;
        delete from ecu;
        delete from engine;
        delete from vehicle;
        delete from manufacturer;
        delete from dtc_standard;
        delete from diag_protocol;
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

                mid = self._get_or_insert(conn, "manufacturer", "name", manufacturer)

                conn.execute(
                    "insert into ecu(manufacturer_id,model) values(?,?)",
                    (mid, model),
                )

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

            if isinstance(manufacturers, str):
                manufacturers = [manufacturers]

            if isinstance(protocols, str):
                protocols = [protocols]

            if isinstance(standards, str):
                standards = [standards]

            for m in manufacturers:
                self._get_or_insert(conn, "manufacturer", "name", m)

            cur = conn.cursor()

            created = d.get("created") or datetime.datetime.now().isoformat()
            updated = d.get("updated") or created

            cur.execute(
                """
                insert into dtc(
                    code,
                    system,
                    subsystem,
                    category,
                    definition,
                    description,
                    severity,
                    mil,
                    created,
                    updated,
                    related_code,
                    detection_condition,
                    causes,
                    repairs,
                    evidence
                )
                values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    d.get("code"),
                    d.get("system"),
                    d.get("subsystem"),
                    d.get("category"),
                    d.get("definition"),
                    d.get("description"),
                    d.get("severity"),
                    d.get("mil"),
                    created,
                    updated,
                    json.dumps(d.get("related_code", [])),
                    json.dumps(d.get("detection_condition", [])),
                    json.dumps(d.get("causes", [])),
                    json.dumps(d.get("repairs", [])),
                    json.dumps(d.get("evidence", {})),
                ),
            )

            dtc_id = cur.lastrowid

            for s in standards:
                sid = self._get_or_insert(conn, "dtc_standard", "name", s)
                conn.execute(
                    "insert into dtc_standard_link values(?,?)",
                    (dtc_id, sid),
                )

            for p in protocols:
                pid = self._get_or_insert(conn, "diag_protocol", "name", p)
                conn.execute(
                    "insert into dtc_protocol_link values(?,?)",
                    (dtc_id, pid),
                )

        conn.commit()
        conn.close()

        return True