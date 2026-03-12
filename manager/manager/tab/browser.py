import manager.tk.tk as tk
from manager.tk.Tab import Tab
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import csv
import json

class BrowserTab(Tab):

    def __init__(self, parent, data_entry: tk.Entry):
        super().__init__(parent)

        self.data_entry = data_entry
        self.vehicles = []
        self.selected_vehicle = None
        self.filtered_dtcs = []

        left = tk.Frame(self.root)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,8))
        left.columnconfigure(0,weight=1)
        left.rowconfigure(2,weight=1)

        tk.Label(left,text="Search Vehicles:").grid(row=0,column=0,sticky="w")
        self.vehicle_search_var = tk.StringVar()
        self.vehicle_search_var.trace_add("write",lambda *a:self.update_vehicle_filter())
        tk.Entry(left,textvariable=self.vehicle_search_var).grid(row=1,column=0,sticky="we")

        self.vehicles_view = ttk.Treeview(left,columns=("model","years"),show="headings")
        self.vehicles_view.heading("model",text="Model")
        self.vehicles_view.heading("years",text="Years")
        self.vehicles_view.grid(row=2,column=0,sticky="nsew")
        self.vehicles_view.bind("<<TreeviewSelect>>",self.on_vehicle_select)

        btn = tk.Frame(left)
        btn.grid(row=3,column=0,sticky="we")

        tk.Button(btn,text="Add Vehicle",command=self.add_vehicle).grid(row=0,column=0,padx=3,pady=3)
        tk.Button(btn,text="Delete Vehicle",command=self.delete_vehicle).grid(row=0,column=1,padx=3,pady=3)
        tk.Button(btn,text="Reload",command=self.load_vehicles).grid(row=0,column=2,padx=3,pady=3)
        tk.Button(btn,text="Save Changes",command=self.save_changes).grid(row=0,column=3,padx=3,pady=3)

        details = tk.LabelFrame(left,text="Vehicle Details")
        details.grid(row=4,column=0,sticky="we")

        self.entries={}
        for i,k in enumerate(["manufacturer","engine","ecu","years"]):
            tk.Label(details,text=k.capitalize()+":").grid(row=i,column=0,sticky="e")
            e=tk.Entry(details,width=40)
            e.grid(row=i,column=1,sticky="we")
            self.entries[k]=e

        right=tk.Frame(self.root)
        right.grid(row=0,column=1,sticky="nsew")
        right.columnconfigure(0,weight=1)
        right.rowconfigure(2,weight=1)

        tk.Label(right,text="Search DTCs:").grid(row=0,column=0,sticky="w")
        self.dtc_search_var=tk.StringVar()
        self.dtc_search_var.trace_add("write",lambda *a:self.update_dtc_filter())
        tk.Entry(right,textvariable=self.dtc_search_var).grid(row=1,column=0,sticky="we")

        frame=tk.LabelFrame(right,text="DTC List")
        frame.grid(row=2,column=0,sticky="nsew")
        frame.rowconfigure(0,weight=1)
        frame.columnconfigure(0,weight=1)

        self.dtc_listbox=tk.Listbox(frame)
        self.dtc_listbox.grid(row=0,column=0,sticky="nsew")

        btnf=tk.Frame(frame)
        btnf.grid(row=0,column=1,sticky="ns")

        tk.Button(btnf,text="Add",command=self.add_dtc).pack(fill="x")
        tk.Button(btnf,text="Edit",command=self.edit_dtc).pack(fill="x")
        tk.Button(btnf,text="Remove",command=self.remove_dtc).pack(fill="x")
        tk.Button(btnf,text="Import TSV",command=self.import_dtc).pack(fill="x")
        tk.Button(btnf,text="Import CSV",command=self.import_dtc_csv).pack(fill="x")
        tk.Button(btnf,text="Import JSON",command=self.import_dtc_json).pack(fill="x")

        self.load_vehicles()

    def _connect(self):
        return sqlite3.connect(self.data_entry.get())

    def load_vehicles(self):
        conn=self._connect()
        conn.row_factory=sqlite3.Row
        cur=conn.cursor()

        cur.execute("""
        select v.id,
               m.name manufacturer,
               v.model,
               v.years
        from ad_vehicle v
        left join ad_manufacturer m on m.id=v.manufacturer_id
        order by manufacturer,model
        """)

        self.vehicles=[dict(r) for r in cur.fetchall()]
        conn.close()
        self.update_vehicle_filter()

    def update_vehicle_filter(self):
        self.vehicles_view.delete(*self.vehicles_view.get_children())
        q=self.vehicle_search_var.get().lower()

        for v in self.vehicles:
            text=(v["manufacturer"] or "")+" "+(v["model"] or "")
            if q and q not in text.lower():
                continue
            self.vehicles_view.insert("",tk.END,iid=str(v["id"]),values=(text,v["years"]))

    def on_vehicle_select(self,event):
        sel=self.vehicles_view.selection()
        if not sel:
            return
        vid=int(sel[0])
        for v in self.vehicles:
            if v["id"]==vid:
                self.selected_vehicle=v
                break
        self.show_vehicle_details()

    def show_vehicle_details(self):
        if not self.selected_vehicle:
            return
        for k in self.entries:
            self.entries[k].delete(0,tk.END)
        self.entries["manufacturer"].insert(0,self.selected_vehicle["manufacturer"] or "")
        self.entries["years"].insert(0,self.selected_vehicle["years"] or "")
        self.update_dtc_filter()

    def update_dtc_filter(self):
        self.dtc_listbox.delete(0,tk.END)
        if not self.selected_vehicle:
            return

        conn=self._connect()
        cur=conn.cursor()

        cur.execute("""
        select d.code,d.definition
        from ad_dtc d
        join ad_dtc_vehicle_link l on l.dtc_id=d.id
        where l.vehicle_id=?
        order by d.code
        """,(self.selected_vehicle["id"],))

        q=self.dtc_search_var.get().lower()

        for c,d in cur.fetchall():
            if q and q not in c.lower() and q not in (d or "").lower():
                continue
            self.filtered_dtcs.append((c,d))
            self.dtc_listbox.insert(tk.END,f"{c}\t{d}")

        conn.close()

    def add_vehicle(self):
        name=simpledialog.askstring("Vehicle","Model:")
        if not name:
            return
        conn=self._connect()
        cur=conn.cursor()
        cur.execute("insert into ad_vehicle(model) values(?)",(name,))
        conn.commit()
        conn.close()
        self.load_vehicles()

    def delete_vehicle(self):
        if not self.selected_vehicle:
            return
        conn=self._connect()
        cur=conn.cursor()
        cur.execute("delete from ad_vehicle where id=?",(self.selected_vehicle["id"],))
        conn.commit()
        conn.close()
        self.selected_vehicle=None
        self.load_vehicles()

    def save_changes(self):
        if not self.selected_vehicle:
            return

        conn=self._connect()
        cur=conn.cursor()

        manufacturer=self.entries["manufacturer"].get().strip()
        years=self.entries["years"].get().strip()

        cur.execute("select id from ad_manufacturer where name=?",(manufacturer,))
        r=cur.fetchone()

        if r:
            mid=r[0]
        else:
            cur.execute("insert into ad_manufacturer(name) values(?)",(manufacturer,))
            mid=cur.lastrowid

        cur.execute(
        "update ad_vehicle set manufacturer_id=?,years=? where id=?",
        (mid,years,self.selected_vehicle["id"])
        )

        conn.commit()
        conn.close()
        self.load_vehicles()

    def add_dtc(self):
        if not self.selected_vehicle:
            return
        code=simpledialog.askstring("Code","DTC Code")
        if not code:
            return
        desc=simpledialog.askstring("Description","Definition") or ""

        conn=self._connect()
        cur=conn.cursor()

        cur.execute("insert or ignore into ad_dtc(code,definition) values(?,?)",(code,desc))
        cur.execute("select id from ad_dtc where code=?",(code,))
        dtc_id=cur.fetchone()[0]

        cur.execute(
        "insert or ignore into ad_dtc_vehicle_link(vehicle_id,dtc_id) values(?,?)",
        (self.selected_vehicle["id"],dtc_id)
        )

        conn.commit()
        conn.close()
        self.update_dtc_filter()

    def edit_dtc(self):
        sel=self.dtc_listbox.curselection()
        if not sel:
            return
        code,desc=self.filtered_dtcs[sel[0]]

        ncode=simpledialog.askstring("Code","Edit Code:",initialvalue=code)
        if not ncode:
            return
        ndesc=simpledialog.askstring("Description","Edit Definition:",initialvalue=desc)

        conn=self._connect()
        cur=conn.cursor()
        cur.execute("update ad_dtc set code=?,definition=? where code=?",(ncode,ndesc,code))
        conn.commit()
        conn.close()
        self.update_dtc_filter()

    def remove_dtc(self):
        sel=self.dtc_listbox.curselection()
        if not sel:
            return
        code,_=self.filtered_dtcs[sel[0]]

        conn=self._connect()
        cur=conn.cursor()

        cur.execute("select id from ad_dtc where code=?",(code,))
        r=cur.fetchone()
        if not r:
            return
        dtc_id=r[0]

        cur.execute(
        "delete from ad_dtc_vehicle_link where vehicle_id=? and dtc_id=?",
        (self.selected_vehicle["id"],dtc_id)
        )

        conn.commit()
        conn.close()
        self.update_dtc_filter()

    def import_dtc(self):
        if not self.selected_vehicle:
            return
        f=filedialog.askopenfilename(filetypes=[("TSV","*.tsv")])
        if not f:
            return
        with open(f,"r",encoding="utf8") as fp:
            for l in fp:
                p=l.strip().split("\t",1)
                code=p[0]
                desc=p[1] if len(p)==2 else ""
                self._insert_dtc(code,desc)
        self.update_dtc_filter()

    def import_dtc_csv(self):
        if not self.selected_vehicle:
            return
        f=filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
        if not f:
            return
        with open(f,newline="",encoding="utf8") as fp:
            for r in csv.DictReader(fp):
                code=(r.get("code") or "").strip()
                desc=(r.get("description") or "").strip()
                if code:
                    self._insert_dtc(code,desc)
        self.update_dtc_filter()

    def import_dtc_json(self):
        if not self.selected_vehicle:
            return
        f=filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not f:
            return
        with open(f,"r",encoding="utf8") as fp:
            data=json.load(fp)
            for i in data:
                code=str(i.get("code","")).strip()
                desc=str(i.get("description","")).strip()
                if code:
                    self._insert_dtc(code,desc)
        self.update_dtc_filter()

    def _insert_dtc(self,code,desc):
        conn=self._connect()
        cur=conn.cursor()

        cur.execute("insert or ignore into ad_dtc(code,definition) values(?,?)",(code,desc))
        cur.execute("select id from ad_dtc where code=?",(code,))
        dtc_id=cur.fetchone()[0]

        cur.execute(
        "insert or ignore into ad_dtc_vehicle_link(vehicle_id,dtc_id) values(?,?)",
        (self.selected_vehicle["id"],dtc_id)
        )

        conn.commit()
        conn.close()