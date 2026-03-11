import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import ttk, messagebox
from pathlib import Path
import sqlite3
import json
from manager.tab.widget.mod_dtc_panel import ModifyDTCPanel

class QueryTab(Tab):
    def __init__(self, parent, sqlite_path_var: tk.StringVar):
        super().__init__(parent)
        self.sqlite_path_var = sqlite_path_var

        top_container = tk.Frame(self.root)
        top_container.pack(fill="both")

        top_container_left = tk.Frame(top_container)
        top_container_left.pack(fill="both", side="left")

        top_container_right = tk.Frame(top_container)
        top_container_right.pack(fill="both", side="right")

        # Filter frame
        filter_frame = tk.LabelFrame(top_container_left, text="Filter Options")
        filter_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(filter_frame, text="Manufacturer:").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.manufacturer_var = tk.StringVar()
        self.manufacturer_entry = tk.Entry(filter_frame, textvariable=self.manufacturer_var)
        self.manufacturer_entry.grid(row=0, column=1, sticky="we", padx=2, pady=2)
        self.manufacturer_entry.bind("<Return>", lambda e: self.query_dtc())

        tk.Label(filter_frame, text="Engine:").grid(row=1, column=0, sticky="e", padx=2, pady=2)
        self.engine_var = tk.StringVar()
        self.engine_entry = tk.Entry(filter_frame, textvariable=self.engine_var)
        self.engine_entry.grid(row=1, column=1, sticky="we", padx=2, pady=2)
        self.engine_entry.bind("<Return>", lambda e: self.query_dtc())

        filter_frame.columnconfigure(1, weight=1)

        # Query input
        query_frame = tk.Frame(top_container_left)
        query_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(query_frame, text="Enter DTC code:").pack(side="left")
        self.dtc_code_var = tk.StringVar()
        self.dtc_code_entry = tk.Entry(query_frame, textvariable=self.dtc_code_var, width=15)
        self.dtc_code_entry.pack(side="left", padx=5)
        tk.Button(query_frame, text="Search", command=self.query_dtc).pack(side="left")
        self.dtc_code_entry.bind("<Return>", lambda e: self.query_dtc())

        # Explanation label
        self.explanation_label = tk.Label(top_container_left, text="", justify="left", fg="blue", wraplength=600)
        self.explanation_label.pack(fill="x", padx=5, pady=5)

        # Results listbox with scrollbar
        results_frame = tk.LabelFrame(top_container_left, text="Matching DTC Descriptions")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.results_listbox = tk.Listbox(results_frame, height=15)
        self.results_listbox.pack(side="left", fill="both", expand=True, padx=(0,5), pady=5)
        self.results_listbox.bind("<Double-Button-1>", lambda e: self.dtc_on_select())
        results_scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=self.results_listbox.yview)
        results_scrollbar.pack(side="right", fill="y")
        self.results_listbox.config(yscrollcommand=results_scrollbar.set)

        self.modify_panel = ModifyDTCPanel(top_container_right, sqlite_path_var)
        self.modify_panel.pack(side="left", fill="both", expand=True, pady=5, padx=5)

    # Then in query_dtc, bind selection to load panel:
    def dtc_on_select(self):
        selection = self.results_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        dtc_id = self.rows[index]["dtc_id"]  # store self.rows = rows after query
        self.modify_panel.load_dtc(dtc_id)

    def query_dtc(self):
        code_query = self.dtc_code_var.get().strip().upper()
        if not code_query:
            messagebox.showwarning("Input Needed", "Please enter a DTC code.")
            return

        manufacturer_filter = self.manufacturer_var.get().strip().lower()
        engine_filter = self.engine_var.get().strip().lower()

        sqlite_file = Path(self.sqlite_path_var.get())
        if not sqlite_file.exists():
            messagebox.showerror("Database Error", "SQLite database not found.")
            return

        conn = sqlite3.connect(sqlite_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Build query with joins
        query = """
            select 
    d.id as dtc_id,
    d.code,
    d.definition,
    m.name as manufacturer,
    group_concat(distinct s.name) as standards,
    group_concat(distinct p.name) as protocols,
    group_concat(distinct sys.name) as systems,
    group_concat(distinct sub.name) as subsystems,
    group_concat(distinct cat.name) as categories,
    group_concat(distinct sev.name) as severities,
    group_concat(distinct e.model) as ecus,
    group_concat(distinct en.model) as engines,
    group_concat(distinct rd.code) as related_codes
from ad_dtc d
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
left join ad_dtc_ecu_link ecu_link on ecu_link.dtc_id = d.id
left join ad_ecu e on e.id = ecu_link.ecu_id
left join ad_manufacturer m 
    on m.id = e.manufacturer_id
    and lower(m.name) like ?
left join ad_dtc_engine_link eng_link on eng_link.dtc_id = d.id
left join ad_engine en on en.id = eng_link.engine_id
left join ad_dtc_related rd_link on rd_link.dtc_id = d.id
left join ad_dtc rd on rd.id = rd_link.related_dtc_id
where upper(d.code) = ?
group by d.id
        """
        manufacturer_param = f"%{manufacturer_filter}%" if manufacturer_filter else "%"
        cur.execute(query, (manufacturer_param, code_query))

        rows = cur.fetchall()
        conn.close()

        self.rows = rows

        self.results_listbox.delete(0, tk.END)
        if not rows:
            self.explanation_label.config(text=self._explain_code(code_query) + "\n\nNo matching DTC found for the selected filters.")
            return

        for r in rows:
            display_desc = r["definition"] if r["definition"] else "(No description)"
            self.results_listbox.insert(tk.END, f"{r['manufacturer'] or 'Unknown'}: {r['code']} - {display_desc}")

        self.explanation_label.config(text=self._explain_code(code_query))

    def _explain_code(self, code: str) -> str:
        if not code:
            return ""
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
        explanation += "\nExample: P0012 : Camshaft Position Timing Over-Advanced or System Performance (generic fault)\n"
        return explanation