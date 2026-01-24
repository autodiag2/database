import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import ttk, messagebox
from pathlib import Path
from manager.vehicle import Vehicle

class QueryTab(Tab):
    def __init__(self, parent, data_entry: tk.Entry):
        super().__init__(parent)

        self.data_entry = data_entry
        self.vehicles = []
        self.filtered_vehicles = []
        self.filtered_dtcs = []

        # Filter frame
        filter_frame = tk.LabelFrame(self.root, text="Filter Options")
        filter_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(filter_frame, text="Manufacturer:").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.manufacturer_var = tk.StringVar()
        self.manufacturer_entry = tk.Entry(filter_frame, textvariable=self.manufacturer_var)
        self.manufacturer_entry.grid(row=0, column=1, sticky="we", padx=2, pady=2)

        tk.Label(filter_frame, text="Engine:").grid(row=1, column=0, sticky="e", padx=2, pady=2)
        self.engine_var = tk.StringVar()
        self.engine_entry = tk.Entry(filter_frame, textvariable=self.engine_var)
        self.engine_entry.grid(row=1, column=1, sticky="we", padx=2, pady=2)

        filter_frame.columnconfigure(1, weight=1)

        # Query input
        query_frame = tk.Frame(self.root)
        query_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(query_frame, text="Enter DTC code:").pack(side="left")
        self.dtc_code_var = tk.StringVar()
        self.dtc_code_entry = tk.Entry(query_frame, textvariable=self.dtc_code_var, width=15)
        self.dtc_code_entry.pack(side="left", padx=5)
        tk.Button(query_frame, text="Search", command=self.query_dtc).pack(side="left")

        # Explanation label
        self.explanation_label = tk.Label(self.root, text="", justify="left", fg="blue", wraplength=600)
        self.explanation_label.pack(fill="x", padx=5, pady=5)

        # Results listbox with scrollbar
        results_frame = tk.LabelFrame(self.root, text="Matching DTC Descriptions")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.results_listbox = tk.Listbox(results_frame, height=15)
        self.results_listbox.pack(side="left", fill="both", expand=True, padx=(0,5), pady=5)

        results_scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=self.results_listbox.yview)
        results_scrollbar.pack(side="right", fill="y")
        self.results_listbox.config(yscrollcommand=results_scrollbar.set)

        self.load_vehicles()

    def getRootPath(self):
        return Path(self.data_entry.get()) / "vehicle"

    def load_vehicles(self):
        self.vehicles.clear()
        root = self.getRootPath()
        if not root.exists():
            return
        for desc_file in root.rglob("desc.ini"):
            vpath = desc_file.parent
            v = Vehicle(vpath)
            self.vehicles.append(v)
        self.filtered_vehicles = self.vehicles

    def query_dtc(self):
        code_query = self.dtc_code_var.get().strip().upper()
        if not code_query:
            messagebox.showwarning("Input Needed", "Please enter a DTC code.")
            return

        manufacturer_filter = self.manufacturer_var.get().strip().lower()
        engine_filter = self.engine_var.get().strip().lower()

        matches = []
        for vehicle in self.vehicles:
            man = vehicle.data.get("manufacturer", "").lower()
            eng = vehicle.data.get("engine", "").lower()

            if manufacturer_filter and manufacturer_filter not in man:
                continue
            if engine_filter and engine_filter not in eng:
                continue

            for code, desc in vehicle.dtcs:
                if code.upper() == code_query:
                    matches.append((vehicle.data.get("manufacturer", vehicle.path.name), code, desc))

        self.results_listbox.delete(0, tk.END)
        if not matches:
            self.explanation_label.config(text=self._explain_code(code_query) + "\n\nNo matching DTC found for the selected filters.")
            return

        for man, code, desc in matches:
            display_desc = desc if desc else "(No description)"
            self.results_listbox.insert(tk.END, f"{man}: {code} - {display_desc}")

        self.explanation_label.config(text=self._explain_code(code_query))

    def _explain_code(self, code: str) -> str:
        if not code:
            return ""

        # Basic explanation of DTC code structure (generic example)
        first_char = code[0] if len(code) > 0 else ""
        if first_char not in "PBCU":
            return "DTC codes typically start with one of P, B, C, or U."

        explanation = (
            f"Explanation of DTC code structure:\n"
            f"{code} :\n"
            f"- {first_char} = System: P=Powertrain, B=Body, C=Chassis, U=Network\n"
        )

        if len(code) >= 5:
            second_char = code[1]
            explanation += f"- {second_char} = 0 for generic, 1 for manufacturer-specific\n"
            explanation += "- Next three digits = specific fault code\n"

        explanation += "\nPowertrain fault example:\nP0012 : Camshaft Position Timing Over-Advanced or System Performance (generic fault)\n"

        return explanation
