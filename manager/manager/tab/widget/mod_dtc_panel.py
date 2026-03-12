import manager.tk.tk as tk
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

        self.entries = {}
        fields = [
            "code","system","subsystem","category","definition",
            "description","severity","mil","related_code",
            "detection_condition","causes","repairs","evidence",
            "manufacturer","standards","protocols"
        ]

        for i,f in enumerate(fields):
            tk.Label(self,text=f).grid(row=i,column=0,sticky="e",padx=2,pady=2)
            e = tk.Entry(self,width=60)
            e.grid(row=i,column=1,sticky="we",padx=2,pady=2)
            self.entries[f] = e

        self.columnconfigure(1,weight=1)

        tk.Button(self,text="Save Changes",command=self.save_changes).grid(
            row=len(fields),column=0,columnspan=2,pady=10
        )

    def _list(self,cur,sql,dtc_id):
        cur.execute(sql,(dtc_id,))
        return [r[0] for r in cur.fetchall()]

    def load_dtc(self,dtc_id:int):

        self.current_dtc_id = dtc_id
        sqlite_file = Path(self.sqlite_path_var.get())
        if not sqlite_file.exists():
            messagebox.showerror("Database Error","SQLite database not found.")
            return

        conn = sqlite3.connect(sqlite_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("select * from ad_dtc where id=?",(dtc_id,))
        dtc = cur.fetchone()
        if not dtc:
            conn.close()
            messagebox.showerror("Error","DTC not found.")
            return

        manufacturer = ""
        cur.execute("""
        select distinct m.name
        from ad_dtc_vehicle_link dv
        join ad_vehicle v on v.id=dv.vehicle_id
        join ad_manufacturer m on m.id=v.manufacturer_id
        where dv.dtc_id=?
        """,(dtc_id,))
        r = cur.fetchone()
        if r:
            manufacturer = r[0]

        standards = self._list(cur,
        "select s.name from ad_dtc_standard_link l join ad_dtc_standard s on s.id=l.standard_id where l.dtc_id=?",
        dtc_id)

        protocols = self._list(cur,
        "select p.name from ad_dtc_protocol_link l join ad_diag_protocol p on p.id=l.protocol_id where l.dtc_id=?",
        dtc_id)

        systems = self._list(cur,
        "select s.name from ad_dtc_system_link l join ad_dtc_system s on s.id=l.system_id where l.dtc_id=?",
        dtc_id)

        subsystems = self._list(cur,
        "select s.name from ad_dtc_subsystem_link l join ad_dtc_subsystem s on s.id=l.subsystem_id where l.dtc_id=?",
        dtc_id)

        categories = self._list(cur,
        "select c.name from ad_dtc_category_link l join ad_dtc_category c on c.id=l.category_id where l.dtc_id=?",
        dtc_id)

        severities = self._list(cur,
        "select s.name from ad_dtc_severity_link l join ad_dtc_severity s on s.id=l.severity_id where l.dtc_id=?",
        dtc_id)

        related = self._list(cur,
        "select d.code from ad_dtc_related r join ad_dtc d on d.id=r.related_dtc_id where r.dtc_id=?",
        dtc_id)

        conn.close()

        simple = ["code","definition","description","mil"]

        for f in simple:
            val = dtc[f] or ""
            self.entries[f].delete(0,tk.END)
            self.entries[f].insert(0,val)

        json_fields = ["detection_condition","causes","repairs","evidence"]

        for f in json_fields:
            val = dtc[f] or ""
            try:
                val = json.dumps(json.loads(val),indent=2)
            except:
                pass
            self.entries[f].delete(0,tk.END)
            self.entries[f].insert(0,val)

        self.entries["system"].delete(0,tk.END)
        self.entries["system"].insert(0,", ".join(systems))

        self.entries["subsystem"].delete(0,tk.END)
        self.entries["subsystem"].insert(0,", ".join(subsystems))

        self.entries["category"].delete(0,tk.END)
        self.entries["category"].insert(0,", ".join(categories))

        self.entries["severity"].delete(0,tk.END)
        self.entries["severity"].insert(0,", ".join(severities))

        self.entries["related_code"].delete(0,tk.END)
        self.entries["related_code"].insert(0,", ".join(related))

        self.entries["manufacturer"].delete(0,tk.END)
        self.entries["manufacturer"].insert(0,manufacturer)

        self.entries["standards"].delete(0,tk.END)
        self.entries["standards"].insert(0,", ".join(standards))

        self.entries["protocols"].delete(0,tk.END)
        self.entries["protocols"].insert(0,", ".join(protocols))

    def _update_link(self,conn,table_link,table_val,col,val_list,dtc_id):

        cur = conn.cursor()
        cur.execute(f"delete from {table_link} where dtc_id=?",(dtc_id,))

        for name in val_list:
            cur.execute(f"select id from {table_val} where name=?",(name,))
            r = cur.fetchone()
            if r:
                vid = r[0]
            else:
                cur.execute(f"insert into {table_val}(name) values(?)",(name,))
                vid = cur.lastrowid
            cur.execute(f"insert into {table_link}(dtc_id,{col}) values(?,?)",(dtc_id,vid))

    def save_changes(self):

        if self.current_dtc_id is None:
            return

        sqlite_file = Path(self.sqlite_path_var.get())
        if not sqlite_file.exists():
            messagebox.showerror("Database Error","SQLite database not found.")
            return

        conn = sqlite3.connect(sqlite_file)
        cur = conn.cursor()

        values = {
            "code":self.entries["code"].get().strip(),
            "definition":self.entries["definition"].get().strip(),
            "description":self.entries["description"].get().strip(),
            "mil":self.entries["mil"].get().strip(),
            "updated":datetime.datetime.now().isoformat()
        }

        for f in ["detection_condition","causes","repairs","evidence"]:
            v = self.entries[f].get().strip()
            try:
                values[f] = json.dumps(json.loads(v))
            except:
                values[f] = json.dumps([v]) if v else json.dumps([])

        set_clause = ", ".join(f"{k}=?" for k in values.keys())
        cur.execute(
            f"update ad_dtc set {set_clause} where id=?",
            (*values.values(),self.current_dtc_id)
        )

        systems = [s.strip() for s in self.entries["system"].get().split(",") if s.strip()]
        subsystems = [s.strip() for s in self.entries["subsystem"].get().split(",") if s.strip()]
        categories = [s.strip() for s in self.entries["category"].get().split(",") if s.strip()]
        severities = [s.strip() for s in self.entries["severity"].get().split(",") if s.strip()]
        standards = [s.strip() for s in self.entries["standards"].get().split(",") if s.strip()]
        protocols = [s.strip() for s in self.entries["protocols"].get().split(",") if s.strip()]
        related = [s.strip() for s in self.entries["related_code"].get().split(",") if s.strip()]

        self._update_link(conn,"ad_dtc_system_link","ad_dtc_system","system_id",systems,self.current_dtc_id)
        self._update_link(conn,"ad_dtc_subsystem_link","ad_dtc_subsystem","subsystem_id",subsystems,self.current_dtc_id)
        self._update_link(conn,"ad_dtc_category_link","ad_dtc_category","category_id",categories,self.current_dtc_id)
        self._update_link(conn,"ad_dtc_severity_link","ad_dtc_severity","severity_id",severities,self.current_dtc_id)
        self._update_link(conn,"ad_dtc_standard_link","ad_dtc_standard","standard_id",standards,self.current_dtc_id)
        self._update_link(conn,"ad_dtc_protocol_link","ad_diag_protocol","protocol_id",protocols,self.current_dtc_id)

        cur.execute("delete from ad_dtc_related where dtc_id=?", (self.current_dtc_id,))
        for code in related:
            cur.execute("select id from ad_dtc where code=?", (code,))
            r = cur.fetchone()
            if r:
                cur.execute(
                    "insert into ad_dtc_related(dtc_id,related_dtc_id) values(?,?)",
                    (self.current_dtc_id,r[0])
                )

        manufacturer = self.entries["manufacturer"].get().strip()
        if manufacturer:
            cur.execute("select id from ad_manufacturer where name=?", (manufacturer,))
            r = cur.fetchone()
            if r:
                mid = r[0]
            else:
                cur.execute("insert into ad_manufacturer(name) values(?)", (manufacturer,))
                mid = cur.lastrowid

            cur.execute("""
                select v.id
                from ad_dtc_vehicle_link dv
                join ad_vehicle v on v.id=dv.vehicle_id
                where dv.dtc_id=?
                limit 1
            """,(self.current_dtc_id,))
            r = cur.fetchone()

            if r:
                vehicle_id = r[0]
                cur.execute(
                    "update ad_vehicle set manufacturer_id=? where id=?",
                    (mid, vehicle_id)
                )
            else:
                cur.execute(
                    "insert into ad_vehicle(manufacturer_id,model,years) values(?,?,?)",
                    (mid, None, None)
                )
                vehicle_id = cur.lastrowid

                cur.execute(
                    "insert into ad_dtc_vehicle_link(dtc_id,vehicle_id) values(?,?)",
                    (self.current_dtc_id, vehicle_id)
                )

        conn.commit()
        conn.close()

        messagebox.showinfo("Saved","DTC updated successfully.")