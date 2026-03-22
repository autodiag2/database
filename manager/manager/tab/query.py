import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import messagebox
from pathlib import Path
import sqlite3


class QueryTab(Tab):
    def __init__(self, parent, sqlite_path_var: tk.StringVar):
        super().__init__(parent)
        self.sqlite_path_var = sqlite_path_var
        self.rows = []

        top_container = tk.Frame(self.root)
        top_container.pack(fill="both")

        top_container_left = tk.Frame(top_container)
        top_container_left.pack(fill="both", side="left")

        top_container_right = tk.Frame(top_container)
        top_container_right.pack(fill="both", side="right")

        filter_frame = tk.LabelFrame(top_container_left, text="Filter Options")
        filter_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(filter_frame, text="Manufacturer:").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.manufacturer_var = tk.StringVar()
        self.manufacturer_entry = tk.Entry(filter_frame, textvariable=self.manufacturer_var)
        self.manufacturer_entry.grid(row=0, column=1, sticky="we", padx=2, pady=2)
        self.manufacturer_entry.bind("<Return>", lambda e: self.query_dtc())

        tk.Label(filter_frame, text="ECU:").grid(row=1, column=0, sticky="e", padx=2, pady=2)
        self.ecu_var = tk.StringVar()
        self.ecu_entry = tk.Entry(filter_frame, textvariable=self.ecu_var)
        self.ecu_entry.grid(row=1, column=1, sticky="we", padx=2, pady=2)
        self.ecu_entry.bind("<Return>", lambda e: self.query_dtc())

        filter_frame.columnconfigure(1, weight=1)

        query_frame = tk.Frame(top_container_left)
        query_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(query_frame, text="Enter DTC code:").pack(side="left")
        self.dtc_code_var = tk.StringVar()
        self.dtc_code_entry = tk.Entry(query_frame, textvariable=self.dtc_code_var, width=15)
        self.dtc_code_entry.pack(side="left", padx=5)
        tk.Button(query_frame, text="Search", command=self.query_dtc).pack(side="left")
        self.dtc_code_entry.bind("<Return>", lambda e: self.query_dtc())

        self.explanation_label = tk.Label(
            top_container_left,
            text="",
            justify="left",
            fg="blue",
            wraplength=600
        )
        self.explanation_label.pack(fill="x", padx=5, pady=5)

        results_frame = tk.LabelFrame(top_container_left, text="Matching DTC Descriptions")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.results_listbox = tk.Listbox(results_frame, height=15)
        self.results_listbox.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)
        self.results_listbox.bind("<Double-Button-1>", lambda e: self.dtc_on_select())

        results_scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=self.results_listbox.yview)
        results_scrollbar.pack(side="right", fill="y")
        self.results_listbox.config(yscrollcommand=results_scrollbar.set)

    def dtc_on_select(self):
        selection = self.results_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        dtc_id = self.rows[index]["dtc_id"]

    def query_dtc(self):
        code_query = self.dtc_code_var.get().strip().upper()
        if not code_query:
            messagebox.showwarning("Input Needed", "Please enter a DTC code.")
            return

        manufacturer_filter = self.manufacturer_var.get().strip().lower()
        ecu_filter = self.ecu_var.get().strip().lower()

        sqlite_file = Path(self.sqlite_path_var.get())
        if not sqlite_file.exists():
            messagebox.showerror("Database Error", "SQLite database not found.")
            return

        conn = sqlite3.connect(sqlite_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = """
            select
                d.id as dtc_id,
                d.code,
                d.definition,
                d.description,
                m.name as manufacturer,
                e.model as ecu_model,
                e.type as ecu_type,
                group_concat(distinct s.name) as standards,
                group_concat(distinct p.name) as protocols,
                group_concat(distinct sys.name) as systems,
                group_concat(distinct sub.name) as subsystems,
                group_concat(distinct cat.name) as categories,
                group_concat(distinct sev.name) as severities,
                group_concat(distinct rd.code) as related_codes
            from ad_dtc d
            left join ad_ecu e on e.id = d.ecu_id
            left join ad_manufacturer m on m.id = e.manufacturer_id

            left join ad_dtc_standard_link s_link on s_link.dtc_id = d.id
            left join ad_dtc_standard s on s.id = s_link.standard_id

            left join ad_dtc_protocol_link p_link on p_link.dtc_id = d.id
            left join ad_diag_protocol p on p.id = p_link.protocol_id

            left join ad_dtc_system_link sys_link on sys_link.dtc_id = d.id
            left join ad_dtc_system sys on sys.id = sys_link.system_id

            left join ad_dtc_subsystem_link sub_link on sub_link.dtc_id = d.id
            left join ad_dtc_subsystem sub on sub.id = sub_link.subsystem_id

            left join ad_dtc_category_link cat_link on cat_link.dtc_id = d.id
            left join ad_dtc_category cat on cat.id = cat_link.category_id

            left join ad_dtc_severity_link sev_link on sev_link.dtc_id = d.id
            left join ad_dtc_severity sev on sev.id = sev_link.severity_id

            left join ad_dtc_related rd_link on rd_link.dtc_id = d.id
            left join ad_dtc rd on rd.id = rd_link.related_dtc_id

            where upper(d.code) = ?
              and lower(coalesce(m.name, '')) like ?
              and lower(coalesce(e.model, '')) like ?
            group by
                d.id,
                d.code,
                d.definition,
                d.description,
                m.name,
                e.model,
                e.type
            order by
                m.name,
                e.model,
                d.code
        """

        manufacturer_param = f"%{manufacturer_filter}%" if manufacturer_filter else "%"
        ecu_param = f"%{ecu_filter}%" if ecu_filter else "%"

        cur.execute(query, (code_query, manufacturer_param, ecu_param))
        rows = cur.fetchall()
        conn.close()

        self.rows = rows
        self.results_listbox.delete(0, tk.END)

        if not rows:
            self.explanation_label.config(
                text=self._explain_code(code_query) + "\n\nNo matching DTC found for the selected filters."
            )
            return

        for r in rows:
            manufacturer = r["manufacturer"] or "Unknown"
            ecu_model = r["ecu_model"] or "Unknown ECU"
            definition = r["definition"] if r["definition"] else "(No description)"
            self.results_listbox.insert(
                tk.END,
                f"{manufacturer} / {ecu_model}: {r['code']} - {definition}"
            )

        self.explanation_label.config(text=self._explain_code(code_query))

    def _explain_code(self, code: str) -> str:
        if not code:
            return ""

        first_char = code[0] if 0 < len(code) else ""
        if first_char not in "PBCU":
            return "DTC codes typically start with one of P, B, C, or U."

        explanation = (
            f"Explanation of DTC code structure:\n"
            f"{code} :\n"
            f"- {first_char} = System: P=Powertrain, B=Body, C=Chassis, U=Network\n"
        )

        if 5 <= len(code):
            second_char = code[1]
            explanation += f"- {second_char} = 0 for generic, 1 for manufacturer-specific\n"
            explanation += "- Next three digits = specific fault code\n"

        explanation += "\nExample: P0012 : Camshaft Position Timing Over-Advanced or System Performance (generic fault)\n"
        return explanation