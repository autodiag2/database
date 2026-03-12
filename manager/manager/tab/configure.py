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

        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(anchor="w", padx=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=400, mode="determinate")
        self.progress.pack(anchor="w", padx=10, pady=5)

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
