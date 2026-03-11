import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import ttk, messagebox
from pathlib import Path
import sqlite3
import json
import datetime


class ModifyDTCPanel(tk.Frame):
    def __init__(self, parent, sqlite_path_var: tk.StringVar):
        super().__init__(parent)
        self.sqlite_path_var = sqlite_path_var
        self.current_dtc_id = None

        # Scrollable canvas
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner_frame = tk.Frame(canvas)

        self.inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Fields
        self.entries = {}
        fields = [
            "code", "system", "subsystem", "category", "definition",
            "description", "severity", "mil", "related_code",
            "detection_condition", "causes", "repairs", "evidence",
            "manufacturer", "standards", "protocols"
        ]
        for i, f in enumerate(fields):
            tk.Label(self.inner_frame, text=f).grid(row=i, column=0, sticky="e", padx=2, pady=2)
            entry = tk.Entry(self.inner_frame, width=60)
            entry.grid(row=i, column=1, sticky="we", padx=2, pady=2)
            self.entries[f] = entry
        self.inner_frame.columnconfigure(1, weight=1)

        # Save button
        tk.Button(self.inner_frame, text="Save Changes", command=self.save_changes).grid(
            row=len(fields), column=0, columnspan=2, pady=10
        )

    def load_dtc(self, dtc_id: int):
        self.current_dtc_id = dtc_id
        sqlite_file = Path(self.sqlite_path_var.get())
        if not sqlite_file.exists():
            messagebox.showerror("Database Error", "SQLite database not found.")
            return

        conn = sqlite3.connect(sqlite_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get dtc data
        cur.execute("select * from ad_dtc where id=?", (dtc_id,))
        dtc = cur.fetchone()
        if not dtc:
            messagebox.showerror("Error", "DTC not found.")
            conn.close()
            return

        # Get manufacturer
        cur.execute("""
            select m.name
            from ad_manufacturer m
            join ad_dtc d on d.id=?
            left join ad_manufacturer m2 on m2.id=m.id
        """, (dtc_id,))
        m = cur.fetchone()
        manufacturer = m["name"] if m else ""

        # Get standards
        cur.execute("""
            select s.name
            from ad_dtc_standard_link l
            join ad_dtc_standard s on s.id=l.standard_id
            where l.dtc_id=?
        """, (dtc_id,))
        standards = [r["name"] for r in cur.fetchall()]

        # Get protocols
        cur.execute("""
            select p.name
            from ad_dtc_protocol_link l
            join ad_diag_protocol p on p.id=l.protocol_id
            where l.dtc_id=?
        """, (dtc_id,))
        protocols = [r["name"] for r in cur.fetchall()]

        conn.close()

        # Populate entries
        for f in [
            "code", "system", "subsystem", "category", "definition",
            "description", "severity", "mil", "related_code",
            "detection_condition", "causes", "repairs", "evidence"
        ]:
            val = dtc[f]
            if val in (None, ""):
                val = ""
            elif f in ("related_code","detection_condition","causes","repairs","evidence"):
                try:
                    val = json.dumps(json.loads(val), indent=2)
                except:
                    val = str(val)
            self.entries[f].delete(0, tk.END)
            self.entries[f].insert(0, val)

        self.entries["manufacturer"].delete(0, tk.END)
        self.entries["manufacturer"].insert(0, manufacturer)

        self.entries["standards"].delete(0, tk.END)
        self.entries["standards"].insert(0, ", ".join(standards))

        self.entries["protocols"].delete(0, tk.END)
        self.entries["protocols"].insert(0, ", ".join(protocols))

    def save_changes(self):
        if self.current_dtc_id is None:
            return

        sqlite_file = Path(self.sqlite_path_var.get())
        if not sqlite_file.exists():
            messagebox.showerror("Database Error", "SQLite database not found.")
            return

        conn = sqlite3.connect(sqlite_file)
        cur = conn.cursor()

        # Update manufacturer FK
        manufacturer_name = self.entries["manufacturer"].get().strip()
        cur.execute("select id from ad_manufacturer where name=?", (manufacturer_name,))
        row = cur.fetchone()
        if row:
            manufacturer_id = row[0]
        else:
            cur.execute("insert into ad_manufacturer(name) values(?)", (manufacturer_name,))
            manufacturer_id = cur.lastrowid

        # Update DTC
        values = {}
        for f in [
            "code", "system", "subsystem", "category", "definition",
            "description", "severity", "mil"
        ]:
            values[f] = self.entries[f].get().strip()

        # Update JSON fields
        for f in ["related_code","detection_condition","causes","repairs","evidence"]:
            val = self.entries[f].get().strip()
            if val:
                try:
                    val_json = json.dumps(json.loads(val))
                except:
                    val_json = json.dumps([val])
            else:
                val_json = json.dumps([])
            values[f] = val_json

        # Update timestamps
        values["updated"] = datetime.datetime.now().isoformat()

        # Apply update
        set_clause = ", ".join(f"{k}=?" for k in values.keys())
        cur.execute(f"update ad_dtc set {set_clause}, manufacturer_id=? where id=?",
                    (*values.values(), manufacturer_id, self.current_dtc_id))

        # Update standards
        cur.execute("delete from ad_dtc_standard_link where dtc_id=?", (self.current_dtc_id,))
        standards = [s.strip() for s in self.entries["standards"].get().split(",") if s.strip()]
        for s in standards:
            cur.execute("select id from ad_dtc_standard where name=?", (s,))
            row = cur.fetchone()
            if row:
                sid = row[0]
            else:
                cur.execute("insert into ad_dtc_standard(name) values(?)", (s,))
                sid = cur.lastrowid
            cur.execute("insert into ad_dtc_standard_link(dtc_id, standard_id) values(?,?)",
                        (self.current_dtc_id, sid))

        # Update protocols
        cur.execute("delete from ad_dtc_protocol_link where dtc_id=?", (self.current_dtc_id,))
        protocols = [p.strip() for p in self.entries["protocols"].get().split(",") if p.strip()]
        for p in protocols:
            cur.execute("select id from ad_diag_protocol where name=?", (p,))
            row = cur.fetchone()
            if row:
                pid = row[0]
            else:
                cur.execute("insert into ad_diag_protocol(name) values(?)", (p,))
                pid = cur.lastrowid
            cur.execute("insert into ad_dtc_protocol_link(dtc_id, protocol_id) values(?,?)",
                        (self.current_dtc_id, pid))

        conn.commit()
        conn.close()
        messagebox.showinfo("Saved", "DTC updated successfully.")