import manager.tk.tk as tk
from tkinter import ttk
from manager.tk.Tab import Tab
from pathlib import Path
import threading

class ImportTab(Tab):

    def __init__(self, parent, plain_path_var):
        super().__init__(parent)
        self.plain_path_var = plain_path_var

    def get_data_src(self) -> Path:
        return Path(self.plain_path_var.get())