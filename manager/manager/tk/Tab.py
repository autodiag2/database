import manager.tk.tk as tk
from tkinter import ttk
import threading

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

        self.left_pane = tk.Frame(self.root)
        self.left_pane.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(10, 5),
            pady=10
        )

        self.right_pane = tk.Frame(self.root, width=500)
        self.right_pane.pack(
            side="right",
            fill="y",
            padx=(5, 10),
            pady=10
        )
        self.right_pane.pack_propagate(False)

    def search_log(self):

        pattern = self.search_var.get()

        self.log_text.configure(state="normal")

        self.log_text.tag_remove("search", "1.0", "end")
        self.log_text.tag_remove("current_search", "1.0", "end")

        self.search_matches = []
        self.search_index = 0
        self.update_search_status()

        if pattern == "":
            self.log_text.configure(state="disabled")
            return

        start = "1.0"

        while True:

            pos = self.log_text.search(
                pattern,
                start,
                stopindex="end",
                nocase=True
            )

            if pos == "":
                break

            end = f"{pos}+{len(pattern)}c"

            self.log_text.tag_add(
                "search",
                pos,
                end
            )

            self.search_matches.append((pos, end))

            start = end

        if self.search_matches:

            start, end = self.search_matches[0]

            self.log_text.tag_add(
                "current_search",
                start,
                end
            )

            self.log_text.tag_remove("sel", "1.0", "end")
            self.log_text.tag_add("sel", start, end)
            self.log_text.mark_set("insert", end)

            self.log_text.see(start)

        self.update_search_status()

        self.log_text.configure(state="disabled")

    def search_next(self, event=None):

        if not self.search_matches:
            self.update_search_status()
            return "break"

        self.search_index += 1

        if self.search_index >= len(self.search_matches):
            self.search_index = 0

        start, end = self.search_matches[self.search_index]

        self.log_text.see(start)

        self.log_text.tag_remove("sel", "1.0", "end")
        self.log_text.tag_add("sel", start, end)
        self.log_text.mark_set("insert", end)
        self.log_text.tag_remove("current_search", "1.0", "end")
        self.log_text.tag_add("current_search", start, end)
        self.update_search_status()

        return "break"

    def _add_log_widget(self, container=None):
        if not container:
            container = self.left_pane
        frame = tk.LabelFrame(container , text="Operations")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        progress_frame = tk.Frame(frame)
        progress_frame.pack(fill="x", padx=5, pady=(0, 5))

        self.progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate"
        )
        self.progress.pack(side="left", fill="x", expand=True)

        self.progress_label = tk.Label(
            progress_frame,
            width=16,
            anchor="e",
            font=("TkFixedFont", 9),
            text="000000 / 000000"
        )
        self.progress_label.pack(side="left", padx=(10, 0))

        self.progress["value"] = 0
        self.progress["maximum"] = 1

        search_frame = tk.Frame(frame)
        search_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(search_frame, text="Search:").pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.search_log())

        self.search_index = 0
        self.search_matches = []

        entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=30
        )
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", self.search_next)

        tk.Button(
            search_frame,
            text="Clear",
            command=lambda: self.search_var.set("")
        ).pack(side="left")

        self.search_status = tk.Label(
            search_frame,
            text=""
        )
        self.search_status.pack(side="left", padx=(10, 0))

        self.log_text = tk.Text(
            frame,
            wrap="word",
            height=12,
            state="disabled"
        )

        scroll = ttk.Scrollbar(frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.log_text.tag_configure(
            "search",
            background="yellow",
            foreground="black"
        )
        self.log_text.tag_configure(
            "current_search",
            background="orange",
            foreground="black"
        )

    def heavy_op_set_steps(self, steps=1):
        self._progress_steps = max(steps, 1)
        self.progress.configure(maximum=self._progress_steps)

    def heavy_op_init(self, steps=1):
        self._progress_current = 0
        self.heavy_op_set_steps(steps)

        self.progress["value"] = 0
        self.progress_label.config(text=f"0 / {self._progress_steps}")

    def heavy_op_start(self, func, steps, *args, **kwargs):
        self.heavy_op_init(steps)

        def worker():
            try:
                func(*args, **kwargs)
            finally:
                self.root.after(
                    0,
                    lambda: self.progress_label.config(
                        text=f"{self._progress_steps} / {self._progress_steps}"
                    )
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def heavy_op_step(self):

        def update():

            if self._progress_current < self._progress_steps:
                self._progress_current += 1

            self.progress["value"] = self._progress_current
            self.progress_label.config(
                text=f"{self._progress_current} / {self._progress_steps}"
            )

        self.root.after(0, update)
        
    def update_search_status(self):
        if not self.search_matches:
            self.search_status.config(text="no matches")
        else:
            self.search_status.config(
                text=f"{self.search_index + 1} of {len(self.search_matches)}"
            )

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.search_log()

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")