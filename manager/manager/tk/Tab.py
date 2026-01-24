import manager.tk.tk as tk
from tkinter import ttk

class Tab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self)
        
        self.vscrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.hscrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hscrollbar.pack(side="bottom", fill="x")
        
        self.scroll_frame = tk.Frame(self.canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vscrollbar.set, xscrollcommand=self.hscrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vscrollbar.pack(side="right", fill="y")
            
        self.root = tk.Frame(self.scroll_frame)
        self.root.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.scroll_frame.columnconfigure(0, weight=1)
        self.scroll_frame.rowconfigure(0, weight=1)

        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        def is_child_scrollable(w):
            while w is not None:
                if isinstance(w, (ttk.Treeview, tk.Listbox, tk.Text, ttk.Combobox)):
                    return True
                w = w.master
            return False

        def on_wheel(e):
            w = e.widget.winfo_containing(e.x_root, e.y_root)
            if is_child_scrollable(w):
                return
            d = e.delta
            if d == 0:
                return
            step = -1 if 0 < d else 1
            self.canvas.yview_scroll(step, "units")

        def on_shift_wheel(e):
            w = e.widget.winfo_containing(e.x_root, e.y_root)
            if is_child_scrollable(w):
                return
            d = e.delta
            if d == 0:
                return
            step = -1 if 0 < d else 1
            self.canvas.xview_scroll(step, "units")

        rootw = self.winfo_toplevel()
        rootw.bind("<MouseWheel>", on_wheel)
        rootw.bind("<Shift-MouseWheel>", on_shift_wheel)