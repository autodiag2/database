import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import filedialog
from pathlib import Path

class ConfigureTab(Tab):
    def __init__(self, parent):
        super().__init__(parent)

        self.folder_path_var = tk.StringVar(value="./data/")
        self.folder_path_var.trace_add("write", lambda *args: self._check_folder_exists())

        # Folder path label + entry
        path_label = tk.Label(self.root, text="Folder Location:")
        path_label.pack(anchor="w", pady=(10,0), padx=10)

        self.path_entry = tk.Entry(self.root, textvariable=self.folder_path_var, width=60)
        self.path_entry.pack(anchor="w", padx=10)
        self.path_entry.bind("<FocusOut>", lambda e: self._check_folder_exists())

        # Button to open folder dialog
        select_button = tk.Button(self.root, text="Select Folder", command=self._on_select_folder)
        select_button.pack(anchor="w", pady=5, padx=10)

        # Status label for folder existence
        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack(anchor="w", padx=10)
        self._check_folder_exists()
        self._update_status_label()

    def _check_folder_exists(self):
        folder = Path(self.folder_path_var.get())
        if not folder.exists() or not folder.is_dir():
            self.status_label.config(text="Folder does not exist.", fg="red")
        else:
            self.status_label.config(text="Folder exists.", fg="green")

    def _update_status_label(self):
        self._check_folder_exists()

    def _on_select_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.folder_path_var.get())
        if folder_selected:
            self.folder_path_var.set(folder_selected)
            self._check_folder_exists()
