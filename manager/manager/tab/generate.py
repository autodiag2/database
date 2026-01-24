import manager.tk as tk
from tkinter import filedialog, messagebox
import subprocess
import sys
from pathlib import Path

class GenerateTab(tk.Frame):
    def __init__(self, parent, data_entry: tk.Entry):
        super().__init__(parent)
        self.data_entry = data_entry

        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        hbar = tk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        hbar.pack(side="bottom", fill="x")
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=hbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = 0

        tk.Label(self.scroll_frame, text="Export DTC database", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(10, 5))
        row += 1

        export_btn = tk.Button(self.scroll_frame, text="Export as SQLite", command=self._export_sqlite)
        export_btn.grid(row=row, column=0, pady=10, sticky="w")

        self.status_var = tk.StringVar(value="Idle")
        tk.Label(self, textvariable=self.status_var, anchor="w", justify="left").pack(fill="x", padx=5, pady=5)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

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

        try:
            res = subprocess.run(cmd, capture_output=True, check=True, text=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

        text = self.status_var.get()
        if res.stdout:
            text += res.stdout
        if res.stderr:
            text += "\nERROR:\n" + res.stderr

        self.status_var.set(text)
