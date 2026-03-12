import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import filedialog
from pathlib import Path
import sqlite3
import yaml
import pathlib
import threading
from tkinter import ttk
from manager.converter_to_sqlite import ConverterToSqlite
from manager.converter_to_yaml import ConverterToYaml
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

class ConfigureTab(Tab):
    def __init__(self, parent):
        super().__init__(parent)

        self.plain_path_var = tk.StringVar(value="./data-src/")
        self.plain_path_var.trace_add("write", lambda *args: self._plain_check_folder_exists())

        # Folder path label + entry
        plain_path_label = tk.Label(self.root, text="plain text database location:")
        plain_path_label.pack(anchor="w", pady=(10,0), padx=10)

        self.plain_path_entry = tk.Entry(self.root, textvariable=self.plain_path_var, width=60)
        self.plain_path_entry.pack(anchor="w", padx=10)
        self.plain_path_entry.bind("<FocusOut>", lambda e: self._plain_check_folder_exists())

        # Button to open folder dialog
        plain_select_button = tk.Button(self.root, text="Select Folder", command=self._plain_on_select_folder)
        plain_select_button.pack(anchor="w", pady=5, padx=10)

        # Status label for folder existence
        self.plain_status_label = tk.Label(self.root, text="")
        self.plain_status_label.pack(anchor="w", padx=10)
        self._plain_check_folder_exists()
        self._plain_update_status_label()

        self.sqlite_path_var = tk.StringVar(value="./ad_database.sqlite")
        self.sqlite_path_var.trace_add("write", lambda *args: self._sqlite_check_exists())

        sqlite_path_label = tk.Label(self.root, text="SQlite database location:")
        sqlite_path_label.pack(anchor="w", pady=(10,0), padx=10)

        self.sqlite_path_entry = tk.Entry(self.root, textvariable=self.sqlite_path_var, width=60)
        self.sqlite_path_entry.pack(anchor="w", padx=10)
        self.sqlite_path_entry.bind("<FocusOut>", lambda e: self._sqlite_check_exists())

        # Button to open folder dialog
        sqlite_select_button = tk.Button(self.root, text="Select Folder", command=self._sqlite_on_select_file)
        sqlite_select_button.pack(anchor="w", pady=5, padx=10)

        # Status label for folder existence
        self.sqlite_status_label = tk.Label(self.root, text="")
        self.sqlite_status_label.pack(anchor="w", padx=10)
        self._sqlite_check_exists()
        self._sqlite_update_status_label()

        # Button to write formated data
        write_to_sqlite_button = tk.Button(self.root, text="Write to sqlite", command=self.on_write_sqlite)
        write_to_sqlite_button.pack(anchor="w", pady=5, padx=10)

        # Button to write formated data
        write_to_yaml_button = tk.Button(self.root, text="Write to Yaml", command=self.on_write_yaml)
        write_to_yaml_button.pack(anchor="w", pady=5, padx=10)

        self._build_vpic_section()

        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(anchor="w", padx=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=400, mode="determinate")
        self.progress.pack(anchor="w", padx=10, pady=5)

    def _build_vpic_section(self):
        section = tk.LabelFrame(self.root, text="build from vpic postgresql data base")
        section.pack(anchor="w", fill="x", pady=(15, 5), padx=10)

        self.pg_host_var = tk.StringVar(value="localhost")
        self.pg_port_var = tk.StringVar(value="5432")
        self.pg_user_var = tk.StringVar(value="postgres")
        self.pg_password_var = tk.StringVar(value="")
        self.pg_dbname_var = tk.StringVar(value="vpic_lite")
        self.pg_schema_var = tk.StringVar(value="vpic")

        rows = [
            ("host:", self.pg_host_var, False),
            ("port:", self.pg_port_var, False),
            ("user:", self.pg_user_var, False),
            ("password:", self.pg_password_var, True),
            ("dbname:", self.pg_dbname_var, False),
            ("schema:", self.pg_schema_var, False),
        ]

        for i, (label, var, is_password) in enumerate(rows):
            tk.Label(section, text=label).grid(row=i, column=0, sticky="e", padx=4, pady=2)
            entry = tk.Entry(section, textvariable=var, width=40, show="*" if is_password else "")
            entry.grid(row=i, column=1, sticky="we", padx=4, pady=2)

        section.columnconfigure(1, weight=1)

        self.pg_status_label = tk.Label(section, text="")
        self.pg_status_label.grid(row=len(rows), column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2))

        tk.Button(
            section,
            text="Load informations into sqlite db",
            command=self.on_load_vpic_into_sqlite
        ).grid(row=len(rows) + 1, column=0, columnspan=2, sticky="w", padx=4, pady=4)

    def _pg_connect(self):
        if _PG_DRIVER is None:
            raise RuntimeError("No PostgreSQL driver found. Install psycopg or psycopg2.")

        kwargs = {
            "host": self.pg_host_var.get().strip(),
            "port": self.pg_port_var.get().strip(),
            "user": self.pg_user_var.get().strip(),
            "password": self.pg_password_var.get(),
            "dbname": self.pg_dbname_var.get().strip(),
        }

        if _PG_DRIVER == "psycopg":
            return psycopg.connect(**kwargs)
        return psycopg2.connect(**kwargs)

    def _connect_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path_var.get())
        conn.execute("pragma foreign_keys = on")
        return conn

    def _ensure_vpic_sqlite_schema(self, conn):
        conn.executescript("""
        create table if not exists vpic_manufacturer(
            id integer primary key,
            name text
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
        """)

    def _load_vpic_background(self):
        try:
            self.root.after(0, lambda: self.pg_status_label.config(text="Connecting...", fg="black"))

            pg_conn = self._pg_connect()
            pg_cur = pg_conn.cursor()

            sqlite_conn = self._connect_sqlite()
            self._ensure_vpic_sqlite_schema(sqlite_conn)
            sqlite_cur = sqlite_conn.cursor()

            schema = self.pg_schema_var.get().strip() or "vpic"

            pg_cur.execute(f"select count(*) from {schema}.manufacturer")
            manufacturer_total = pg_cur.fetchone()[0]

            pg_cur.execute(f"select count(*) from {schema}.wmi")
            wmi_total = pg_cur.fetchone()[0]

            total = manufacturer_total + wmi_total
            self.root.after(0, lambda: self.progress.configure(value=0, maximum=100))

            sqlite_cur.execute("delete from vpic_wmi")
            sqlite_cur.execute("delete from vpic_manufacturer")
            sqlite_conn.commit()

            done = 0

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
                percent = int((done / total) * 100) if total > 0 else 100
                self.root.after(0, lambda p=percent: self.progress.configure(value=p))

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
                percent = int((done / total) * 100) if total > 0 else 100
                self.root.after(0, lambda p=percent: self.progress.configure(value=p))

            sqlite_conn.commit()
            pg_cur.close()
            pg_conn.close()
            sqlite_conn.close()

            self.root.after(0, lambda: self.pg_status_label.config(text="VPIC data loaded into sqlite.", fg="green"))
            self.root.after(0, lambda: self.progress_label.config(text="Success", fg="green"))

        except Exception as e:
            self.root.after(0, lambda: self.pg_status_label.config(text=str(e), fg="red"))
            self.root.after(0, lambda: self.progress_label.config(text="Import failed", fg="red"))

    def _write_sqlite_background(self):
        conv = ConverterToSqlite(
            plain_text_db=Path(self.plain_path_var.get()),
            sqlite_db=Path(self.sqlite_path_var.get())
        )

        # Hook to update progress dynamically
        def progress_hook(current, total):
            percent = int((current / total) * 100)
            self.root.after(0, lambda: self.progress.configure(value=percent))

        if conv.to_sqlite(progress_callback=progress_hook):
            self.progress_label.config(text="Success", fg="green")
        else:
            self.progress_label.config(text="Export failed", fg="red")

    def _write_yaml_background(self):
        conv = ConverterToYaml(
            plain_text_db=Path(self.plain_path_var.get()),
            sqlite_db=Path(self.sqlite_path_var.get())
        )

        # Hook to update progress dynamically
        def progress_hook(current, total):
            percent = int((current / total) * 100)
            self.root.after(0, lambda: self.progress.configure(value=percent))

        if conv.to_yaml(progress_callback=progress_hook):
            self.progress_label.config(text="Success", fg="green")
        else:
            self.progress_label.config(text="Export failed", fg="red")

    def on_load_vpic_into_sqlite(self):
        if not self._sqlite_check_exists():
            self.progress_label.config(text="SQLite not found, configure it", fg="red")
            return

        self.progress_label.config(text="Processing...", fg="black")
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.pg_status_label.config(text="Processing...", fg="black")

        threading.Thread(target=self._load_vpic_background, daemon=True).start()

    def on_write_yaml(self):
        if not self._sqlite_check_exists():
            self.progress_label.config(text="SQLite not found, configure it", fg="red")
            return
        
        self.progress_label.config(text="Processing...", fg="black")
        self.progress["value"] = 0
        self.progress["maximum"] = 100

        # Run converter in background
        threading.Thread(target=self._write_yaml_background, daemon=True).start()

    def on_write_sqlite(self):
        if not self._plain_check_folder_exists():
            self.progress_label.config(text="Plain text not found, configure it", fg="red")
            return
        
        self.progress_label.config(text="Processing...", fg="black")
        self.progress["value"] = 0
        self.progress["maximum"] = 100

        # Run converter in background
        threading.Thread(target=self._write_sqlite_background, daemon=True).start()

    def _sqlite_check_exists(self) -> bool:
        file = Path(self.sqlite_path_var.get())
        if not file.exists() or not file.is_file():
            self.sqlite_status_label.config(text="SQLite does not exist.", fg="red")
            return False
        else:
            self.sqlite_status_label.config(text="SQLite exists.", fg="green")
            return True

    def _sqlite_on_select_file(self):
        file_selected = filedialog.askdirectory(initialdir=self.sqlite_path_var.get())
        if file_selected:
            self.sqlite_path_var.set(file_selected)
            self._sqlite_check_exists()
    
    def _sqlite_update_status_label(self):
        self._sqlite_check_exists()

    def _plain_check_folder_exists(self) -> bool:
        folder = Path(self.plain_path_var.get())
        if not folder.exists() or not folder.is_dir():
            self.plain_status_label.config(text="Folder does not exist.", fg="red")
            return False
        else:
            self.plain_status_label.config(text="Folder exists.", fg="green")
            return True

    def _plain_update_status_label(self):
        self._plain_check_folder_exists()

    def _plain_on_select_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.plain_path_var.get())
        if folder_selected:
            self.plain_path_var.set(folder_selected)
            self._plain_check_folder_exists()
