import manager.tk.tk as tk
from tkinter import ttk
from manager.tk.Tab import Tab
from pathlib import Path

class ImportTab(Tab):

    def __init__(self, parent, plain_path_var):
        super().__init__(parent)

        self.plain_path_var = plain_path_var

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

    def get_data_src(self) -> Path:
        return Path(self.plain_path_var.get())

    def _build_output(self):
        frame = tk.LabelFrame(self.left_pane , text="Operations")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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