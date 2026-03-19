from pathlib import Path
import sqlite3

try:
    import psycopg
    _PG_DRIVER = "psycopg"
except Exception:
    psycopg = None
    try:
        import psycopg2
        _PG_DRIVER = "psycopg2"
    except Exception:
        psycopg2 = None
        _PG_DRIVER = None


class VpicToSqliteLoader:
    def __init__(
        self,
        sqlite_path,
        pg_host="localhost",
        pg_port="5432",
        pg_user="postgres",
        pg_password="",
        pg_dbname="vpic_lite",
        pg_schema="vpic",
    ):
        self.sqlite_path = Path(sqlite_path)
        self.pg_host = str(pg_host).strip()
        self.pg_port = str(pg_port).strip()
        self.pg_user = str(pg_user).strip()
        self.pg_password = pg_password
        self.pg_dbname = str(pg_dbname).strip()
        self.pg_schema = str(pg_schema).strip() or "vpic"

    def _pg_connect(self):
        if _PG_DRIVER is None:
            raise RuntimeError("No PostgreSQL driver found. Install psycopg or psycopg2.")

        kwargs = {
            "host": self.pg_host,
            "port": self.pg_port,
            "user": self.pg_user,
            "password": self.pg_password,
            "dbname": self.pg_dbname,
        }

        if _PG_DRIVER == "psycopg":
            return psycopg.connect(**kwargs)
        return psycopg2.connect(**kwargs)

    def _connect_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("pragma foreign_keys = on")
        return conn

    def _ensure_vpic_sqlite_schema(self, conn):
        conn.executescript("""
        create table if not exists vpic_manufacturer(
            id integer primary key,
            name text
        );
        create table if not exists vpic_country(
            id integer primary key,
            name text,
            displayorder integer
        );
        create table if not exists vpic_wmi(
            id integer primary key,
            wmi text,
            manufacturerid integer,
            makeid integer,
            vehicletypeid integer,
            createdon text,
            updatedon text,
            countryid integer,
            publicavailabilitydate text,
            trucktypeid integer,
            processedon text,
            noncompliant text,
            noncompliantsetbyovsc text
        );

        create index if not exists idx_vpic_wmi_wmi on vpic_wmi(wmi);
        create index if not exists idx_vpic_wmi_manufacturerid on vpic_wmi(manufacturerid);
        create index if not exists idx_vpic_wmi_countryid on vpic_wmi(countryid);
        """)

    def load(self, progress_callback=None):
        pg_conn = None
        pg_cur = None
        sqlite_conn = None
        sqlite_cur = None

        try:
            pg_conn = self._pg_connect()
            pg_cur = pg_conn.cursor()

            sqlite_conn = self._connect_sqlite()
            self._ensure_vpic_sqlite_schema(sqlite_conn)
            sqlite_cur = sqlite_conn.cursor()

            schema = self.pg_schema

            pg_cur.execute(f"select count(*) from {schema}.manufacturer")
            manufacturer_total = pg_cur.fetchone()[0]

            pg_cur.execute(f"select count(*) from {schema}.country")
            country_total = pg_cur.fetchone()[0]

            pg_cur.execute(f"select count(*) from {schema}.wmi")
            wmi_total = pg_cur.fetchone()[0]

            total = manufacturer_total + country_total + wmi_total
            done = 0

            if progress_callback is not None:
                progress_callback(done, total)

            sqlite_cur.execute("delete from vpic_country")
            sqlite_cur.execute("delete from vpic_wmi")
            sqlite_cur.execute("delete from vpic_manufacturer")
            sqlite_conn.commit()

            pg_cur.execute(f"""
                select id, name
                from {schema}.manufacturer
                order by id
            """)
            for row in pg_cur.fetchall():
                sqlite_cur.execute(
                    "insert into vpic_manufacturer(id, name) values(?, ?)",
                    row
                )
                done += 1
                if progress_callback is not None:
                    progress_callback(done, total)

            pg_cur.execute(f"""
                select id, name, displayorder
                from {schema}.country
                order by id
            """)
            for row in pg_cur.fetchall():
                sqlite_cur.execute(
                    "insert into vpic_country(id, name, displayorder) values(?, ?, ?)",
                    row
                )
                done += 1
                if progress_callback is not None:
                    progress_callback(done, total)

            sqlite_conn.commit()

            pg_cur.execute(f"""
                select
                    id,
                    wmi,
                    manufacturerid,
                    makeid,
                    vehicletypeid,
                    createdon::text,
                    updatedon::text,
                    countryid,
                    publicavailabilitydate::text,
                    trucktypeid,
                    processedon::text,
                    noncompliant::text,
                    noncompliantsetbyovsc::text
                from {schema}.wmi
                order by id
            """)
            for row in pg_cur.fetchall():
                sqlite_cur.execute("""
                    insert into vpic_wmi(
                        id,
                        wmi,
                        manufacturerid,
                        makeid,
                        vehicletypeid,
                        createdon,
                        updatedon,
                        countryid,
                        publicavailabilitydate,
                        trucktypeid,
                        processedon,
                        noncompliant,
                        noncompliantsetbyovsc
                    ) values(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, row)
                done += 1
                if progress_callback is not None:
                    progress_callback(done, total)

            sqlite_conn.commit()

            if progress_callback is not None and done < total:
                progress_callback(total, total)

            return True

        finally:
            if pg_cur is not None:
                pg_cur.close()
            if pg_conn is not None:
                pg_conn.close()
            if sqlite_conn is not None:
                sqlite_conn.close()