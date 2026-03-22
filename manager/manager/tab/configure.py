import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import filedialog
from pathlib import Path
import threading
from tkinter import ttk
from manager.converter_to_sqlite import ConverterToSqlite
from manager.vpic_sqlite_loader import VpicToSqliteLoader


class ConfigureTab(Tab):
    def __init__(self, parent):
        super().__init__(parent)

        self.plain_path_var = tk.StringVar(value="./data-src/")
        self.plain_path_var.trace_add("write", lambda *args: self._plain_check_folder_exists())

        plain_path_label = tk.Label(self.root, text="plain text database location:")
        plain_path_label.pack(anchor="w", pady=(10, 0), padx=10)

        self.plain_path_entry = tk.Entry(self.root, textvariable=self.plain_path_var, width=60)
        self.plain_path_entry.pack(anchor="w", padx=10)
        self.plain_path_entry.bind("<FocusOut>", lambda e: self._plain_check_folder_exists())

        plain_select_button = tk.Button(self.root, text="Select Folder", command=self._plain_on_select_folder)
        plain_select_button.pack(anchor="w", pady=5, padx=10)

        self.plain_status_label = tk.Label(self.root, text="")
        self.plain_status_label.pack(anchor="w", padx=10)
        self._plain_check_folder_exists()
        self._plain_update_status_label()

        self.sqlite_path_var = tk.StringVar(value="./data/ad_database.sqlite")
        self.sqlite_path_var.trace_add("write", lambda *args: self._sqlite_check_exists())

        sqlite_path_label = tk.Label(self.root, text="SQlite database location:")
        sqlite_path_label.pack(anchor="w", pady=(10, 0), padx=10)

        self.sqlite_path_entry = tk.Entry(self.root, textvariable=self.sqlite_path_var, width=60)
        self.sqlite_path_entry.pack(anchor="w", padx=10)
        self.sqlite_path_entry.bind("<FocusOut>", lambda e: self._sqlite_check_exists())

        sqlite_select_button = tk.Button(self.root, text="Select Folder", command=self._sqlite_on_select_file)
        sqlite_select_button.pack(anchor="w", pady=5, padx=10)

        self.sqlite_status_label = tk.Label(self.root, text="")
        self.sqlite_status_label.pack(anchor="w", padx=10)
        self._sqlite_check_exists()
        self._sqlite_update_status_label()

        write_to_sqlite_button = tk.Button(self.root, text="Write to sqlite", command=self.on_write_sqlite)
        write_to_sqlite_button.pack(anchor="w", pady=5, padx=10)

        self._build_vpic_section()

        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(anchor="w", padx=10)

        self.progress = ttk.Progressbar(self.root, length=400, mode="determinate")
        self.progress.pack(anchor="w", padx=10, pady=5)

    def _build_vpic_section(self):
        section = tk.LabelFrame(self.root, text="build from vpic postgresql data base")
        section.pack(anchor="w", fill="x", pady=(15, 5), padx=10)

        self.pg_host_var = tk.StringVar(value="localhost")
        self.pg_port_var = tk.StringVar(value="5432")
        self.pg_user_var = tk.StringVar(value="jean")
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

    def _write_sqlite_background(self):
        conv = ConverterToSqlite(
            plain_text_db=Path(self.plain_path_var.get()),
            sqlite_db=Path(self.sqlite_path_var.get())
        )

        def progress_hook(current, total):
            percent = int((current / total) * 100) if 0 < total else 100
            self.root.after(0, lambda: self.progress.configure(value=percent))

        if conv.to_sqlite(progress_callback=progress_hook):
            self.progress_label.config(text="Success", fg="green")
        else:
            self.progress_label.config(text="Export failed", fg="red")

    def _load_vpic_background(self):
        try:
            self.root.after(0, lambda: self.pg_status_label.config(text="Connecting...", fg="black"))

            loader = VpicToSqliteLoader(
                sqlite_path=self.sqlite_path_var.get(),
                pg_host=self.pg_host_var.get(),
                pg_port=self.pg_port_var.get(),
                pg_user=self.pg_user_var.get(),
                pg_password=self.pg_password_var.get(),
                pg_dbname=self.pg_dbname_var.get(),
                pg_schema=self.pg_schema_var.get(),
            )

            def progress_hook(current, total):
                percent = int((current / total) * 100) if 0 < total else 100
                self.root.after(0, lambda: self.progress.configure(value=percent))

            ok = loader.load(progress_callback=progress_hook)

            if ok:
                self.root.after(0, lambda: self.pg_status_label.config(text="VPIC data loaded into sqlite.", fg="green"))
                self.root.after(0, lambda: self.progress_label.config(text="Success", fg="green"))
            else:
                self.root.after(0, lambda: self.pg_status_label.config(text="Failed to load VPIC data.", fg="red"))
                self.root.after(0, lambda: self.progress_label.config(text="Import failed", fg="red"))

        except Exception as e:
            self.root.after(0, lambda: self.pg_status_label.config(text=str(e), fg="red"))
            self.root.after(0, lambda: self.progress_label.config(text="Import failed", fg="red"))

    def on_load_vpic_into_sqlite(self):
        if not self._sqlite_check_exists():
            self.progress_label.config(text="SQLite not found, configure it", fg="red")
            return

        self.progress_label.config(text="Processing...", fg="black")
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.pg_status_label.config(text="Processing...", fg="black")

        threading.Thread(target=self._load_vpic_background, daemon=True).start()

    def on_write_sqlite(self):
        if not self._plain_check_folder_exists():
            self.progress_label.config(text="Plain text not found, configure it", fg="red")
            return

        self.progress_label.config(text="Processing...", fg="black")
        self.progress["value"] = 0
        self.progress["maximum"] = 100

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