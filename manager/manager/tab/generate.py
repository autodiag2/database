import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import filedialog, messagebox
import subprocess
import sys
from pathlib import Path

class GenerateTab(Tab):
    def __init__(self, parent, data_entry: tk.Entry):
        super().__init__(parent)
        self.data_entry = data_entry

        row = 0

        tk.Label(self.root, text="Export DTC database", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(10, 5))
        row += 1

        export_sqlite_btn = tk.Button(self.root, text="Export as SQLite", command=self._export_sqlite)
        export_sqlite_btn.grid(row=row, column=0, pady=(0, 8), sticky="w")
        row += 1

        export_json_btn = tk.Button(self.root, text="Export as JSON (dir layout)", command=self._export_json)
        export_json_btn.grid(row=row, column=0, pady=(0, 10), sticky="w")
        row += 1

        self.status_var = tk.StringVar(value="Idle")
        tk.Label(self, textvariable=self.status_var, anchor="w", justify="left").pack(fill="x", padx=5, pady=5)

    def _export_sqlite(self):
        data_path = Path(self.data_entry.get()).resolve()
        if not data_path.exists():
            self.status_var.set("Data folder does not exist.")
            return

        out_path = filedialog.asksaveasfilename(
            defaultextension=".sqlite",
            title="Export as SQLite",
            filetypes=[("SQLite database", "*.sqlite")],
            initialfile="dtcs"
        )
        if not out_path:
            return

        self.status_var.set("Running...\n")

        cmd = [
            sys.executable,
            "-m",
            "manager.compile_dtcs_database",
            "--repo", str(data_path.parent),
            "--data", str(data_path),
            "--out", out_path,
        ]

        res = None
        try:
            res = subprocess.run(cmd, capture_output=True, check=True, text=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

        text = self.status_var.get()
        if res and res.stdout:
            text += res.stdout
        if res and res.stderr:
            text += "\nERROR:\n" + res.stderr

        self.status_var.set(text)

    def _export_json(self):
        data_path = Path(self.data_entry.get()).resolve()
        if not data_path.exists():
            self.status_var.set("Data folder does not exist.")
            return

        out_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            title="Export as JSON",
            filetypes=[("JSON file", "*.json")],
            initialfile="dtc.json"
        )
        if not out_path:
            return

        self.status_var.set("Running...\n")

        cmd = [
            sys.executable,
            "-m",
            "manager.compile_dtcs_json",
            "--repo", str(data_path.parent),
            "--data", str(data_path),
            "--out", out_path,
        ]

        res = None
        try:
            res = subprocess.run(cmd, capture_output=True, check=True, text=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

        text = self.status_var.get()
        if res and res.stdout:
            text += res.stdout
        if res and res.stderr:
            text += "\nERROR:\n" + res.stderr

        self.status_var.set(text)
