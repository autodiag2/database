import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
from manager.vehicle import Vehicle
import os
import re
import csv
import json
import shutil
import tkinter.font as tkfont

class BrowserTab(tk.Frame):

    def getRootPath(self):
        return Path(self.data_entry.get()) / "vehicle"

    def __init__(self, parent, data_entry: tk.Entry):
        super().__init__(parent)

        self.data_entry = data_entry
        self.vehicles = []
        self.selected_vehicle = None
        self.selected_folder = None
        self.filtered_vehicles = []
        self.filtered_dtcs = []

        self._node_map = {}
        self._folder_item_by_rel = {}
        self._vehicle_item_by_path = {}

        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.scroll_frame.columnconfigure(0, weight=1)
        self.scroll_frame.columnconfigure(1, weight=1)
        self.scroll_frame.rowconfigure(2, weight=1)
        self.scroll_frame.rowconfigure(7, weight=1)

        tk.Label(self.scroll_frame, text="Search Vehicles:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vehicle_search_var = tk.StringVar()
        self.vehicle_search_var.trace_add("write", lambda *a: self.update_vehicle_filter())
        self.vehicle_search_entry = tk.Entry(self.scroll_frame, textvariable=self.vehicle_search_var)
        self.vehicle_search_entry.grid(row=1, column=0, sticky="we", padx=5)

        self.vehicles_view = ttk.Treeview(
            self.scroll_frame,
            columns=("duplicates", "malformed"),
            show="tree headings",
            height=20
        )

        self.vehicles_view.heading("#0", text="Folder / Vehicle")
        self.vehicles_view.heading("duplicates", text="Duplicated DTCs")
        self.vehicles_view.heading("malformed", text="Malformed entries")

        self.vehicles_view.column("#0", stretch=False)
        self.vehicles_view.column("#0", width=200)
        self.vehicles_view.column("duplicates", width=140, anchor="center")
        self.vehicles_view.column("malformed", width=160, anchor="center")
        for c in self.vehicles_view["columns"]:
            self.vehicles_view.column(c, stretch=False)

        self.vehicles_view.tag_configure("duplicates", foreground="orange")
        self.vehicles_view.tag_configure("malformed", foreground="red")
        self.vehicles_view.tag_configure("folder", foreground="gray30")

        self.vehicles_view.grid(row=2, column=0, sticky="nsw", padx=5, pady=5)
        self.vehicles_view.bind("<<TreeviewSelect>>", self.on_vehicle_select)
        self.vehicles_view.bind("<Configure>", lambda e: self.autosize_treeview(self.vehicles_view))

        btn_frame = tk.Frame(self.scroll_frame)
        btn_frame.grid(row=3, column=0, sticky="we", padx=5, pady=5)

        btn_frame = tk.Frame(self.scroll_frame)
        btn_frame.grid(row=3, column=0, sticky="we", padx=5, pady=5)

        buttons = [
            ("Add Vehicle", self.add_vehicle),
            ("Delete Vehicle", self.delete_vehicle),
            ("Add Folder", self.add_folder),
            ("Rename Folder", self.rename_folder),
            ("Delete Folder", self.delete_folder),
            ("Move Vehicle", self.move_vehicle),
            ("Reload", self.load_vehicles),
            ("Save Changes", self.save_changes),
        ]

        cols = 4
        for i, (text, cmd) in enumerate(buttons):
            r = i // cols
            c = i % cols
            b = tk.Button(btn_frame, text=text, command=cmd)
            b.grid(row=r, column=c, padx=3, pady=3, sticky="we")

        for c in range(cols):
            btn_frame.columnconfigure(c, weight=1)

        details_frame = tk.LabelFrame(self.scroll_frame, text="Vehicle Details")
        details_frame.grid(row=0, column=1, sticky="nwe", rowspan=4, padx=5, pady=5)
        details_frame.columnconfigure(1, weight=1)

        self.entries = {}
        for i, key in enumerate(["manufacturer", "engine", "ecu", "years"]):
            tk.Label(details_frame, text=key.capitalize() + ":").grid(row=i, column=0, sticky="e", padx=2, pady=2)
            ent = tk.Entry(details_frame, width=40)
            ent.grid(row=i, column=1, sticky="we", padx=2, pady=2)
            self.entries[key] = ent

        tk.Label(self.scroll_frame, text="Search DTCs:").grid(row=4, column=1, sticky="w", padx=5, pady=2)
        self.dtc_search_var = tk.StringVar()
        self.dtc_search_var.trace_add("write", lambda *a: self.update_dtc_filter())
        self.dtc_search_entry = tk.Entry(self.scroll_frame, textvariable=self.dtc_search_var)
        self.dtc_search_entry.grid(row=5, column=1, sticky="we", padx=5)

        dtc_frame = tk.LabelFrame(self.scroll_frame, text="DTC List")
        dtc_frame.grid(row=6, column=1, sticky="nsew", rowspan=3, padx=5, pady=5)
        dtc_frame.rowconfigure(0, weight=1)
        dtc_frame.columnconfigure(0, weight=1)

        self.dtc_listbox = tk.Listbox(dtc_frame, height=15, width=50)
        self.dtc_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.dtc_listbox.bind("<Double-Button-1>", lambda e: self.edit_dtc())

        dtc_btn_frame = tk.Frame(dtc_frame)
        dtc_btn_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

        tk.Button(dtc_btn_frame, text="Add DTC", command=self.add_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Edit DTC", command=self.edit_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Remove DTC", command=self.remove_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Import DTCs from TSV", command=self.import_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Import DTCs from CSV", command=self.import_dtc_csv).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Import DTCs from JSON", command=self.import_dtc_json).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="View Duplicates", command=self.view_duplicates).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="View Malformed", command=self.view_malformed).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Remove Exact Duplicates", command=self.remove_exact_duplicates).pack(fill="x", pady=2)

        self.load_vehicles()

    def _clear_tree(self):
        self.vehicles_view.delete(*self.vehicles_view.get_children())
        self._node_map.clear()
        self._folder_item_by_rel.clear()
        self._vehicle_item_by_path.clear()

    def _norm_rel_folder(self, p: Path) -> str:
        s = str(p).replace("\\", "/").strip("/")
        if s == ".":
            return ""
        return s
    
    def autosize_treeview(self, tree: ttk.Treeview, max_width=500, pad=18):
        style = ttk.Style()
        f = style.lookup("Treeview", "font")
        font = tkfont.nametofont(f) if f else tkfont.nametofont("TkDefaultFont")

        def text_w(s: str) -> int:
            return font.measure(s if s is not None else "")

        tree_w = 0

        w0 = text_w(tree.heading("#0")["text"]) + pad
        indent = 20

        for iid in tree.get_children(""):
            stack = [iid]
            while stack:
                x = stack.pop()
                depth = 0
                p = tree.parent(x)
                while p:
                    depth += 1
                    p = tree.parent(p)

                w0 = max(w0, text_w(tree.item(x, "text")) + pad + indent * depth)
                stack.extend(tree.get_children(x))

        w0 = min(w0, max_width)
        tree.column("#0", width=w0)
        tree_w += w0

        for col in tree["columns"]:
            wh = text_w(tree.heading(col)["text"]) + pad
            for iid in tree.get_children(""):
                stack = [iid]
                while stack:
                    x = stack.pop()
                    vals = tree.item(x, "values") or ()
                    idx = list(tree["columns"]).index(col)
                    v = vals[idx] if idx < len(vals) else ""
                    wh = max(wh, text_w(str(v)) + pad)
                    stack.extend(tree.get_children(x))
            wh = min(wh, max_width)
            tree.column(col, width=wh)
            tree_w += wh

        return tree_w

    def _get_selected_item_info(self):
        sel = self.vehicles_view.selection()
        if not sel:
            return None
        item_id = sel[0]
        return self._node_map.get(item_id)

    def _get_selected_folder_path(self) -> Path:
        root = self.getRootPath()
        info = self._get_selected_item_info()
        if not info:
            return root
        if info["type"] == "folder":
            return info["path"]
        if info["type"] == "vehicle":
            return info["path"].parent
        return root

    def _ensure_folder_node(self, rel_folder: str):
        rel_folder = self._norm_rel_folder(Path(rel_folder))
        if rel_folder == "":
            return ""
        if rel_folder in self._folder_item_by_rel:
            return self._folder_item_by_rel[rel_folder]

        parent_rel = self._norm_rel_folder(Path(rel_folder).parent)
        if parent_rel == rel_folder:
            parent_rel = ""
        parent_item = self._ensure_folder_node(parent_rel) if parent_rel else ""

        name = Path(rel_folder).name
        item_id = self.vehicles_view.insert(
            parent_item,
            "end",
            text=name,
            values=("", ""),
            tags=("folder",),
            open=True
        )
        abs_path = self.getRootPath() / rel_folder
        self._node_map[item_id] = {"type": "folder", "path": abs_path}
        self._folder_item_by_rel[rel_folder] = item_id
        return item_id

    def _build_display_rows(self, vehicles):
        root = self.getRootPath()
        nodes = {"": {"folders": set(), "vehicles": []}}

        for v in vehicles:
            try:
                rel = v.path.relative_to(root)
            except Exception:
                continue

            rel_parent = self._norm_rel_folder(rel.parent)
            rel_vehicle_dir = self._norm_rel_folder(rel)

            cur = Path(rel_parent)
            while True:
                rel_cur = self._norm_rel_folder(cur)
                rel_par = self._norm_rel_folder(cur.parent)
                if rel_cur != "":
                    nodes.setdefault(rel_par, {"folders": set(), "vehicles": []})["folders"].add(rel_cur)
                    nodes.setdefault(rel_cur, {"folders": set(), "vehicles": []})
                if rel_cur == "":
                    break
                cur = cur.parent

            nodes.setdefault(rel_parent, {"folders": set(), "vehicles": []})["vehicles"].append(v)

        for k in list(nodes.keys()):
            nodes.setdefault(k, {"folders": set(), "vehicles": []})

        return nodes

    def _render_tree(self, vehicles):
        self._clear_tree()

        query = self.vehicle_search_var.get().lower().strip()
        wanted = []
        if query:
            for v in self.vehicles:
                name = (v.data.get("manufacturer", "") or v.path.name).lower()
                rel = ""
                try:
                    rel = str(v.path.relative_to(self.getRootPath())).replace("\\", "/").lower()
                except Exception:
                    rel = v.path.name.lower()
                if query in name or query in rel:
                    wanted.append(v)
        else:
            wanted = list(self.vehicles)

        self.filtered_vehicles = wanted

        nodes = self._build_display_rows(wanted)

        def folder_key(s: str):
            return s.lower()

        def vehicle_key(v: Vehicle):
            disp = v.data.get("manufacturer", "").strip()
            if not disp:
                disp = v.path.name
            return disp.lower()

        def add_children(rel_folder: str, parent_item: str):
            folders = sorted(nodes.get(rel_folder, {}).get("folders", set()), key=folder_key)
            for child_rel in folders:
                child_item = self._ensure_folder_node(child_rel)
                add_children(child_rel, child_item)

            vehicles_here = sorted(nodes.get(rel_folder, {}).get("vehicles", []), key=vehicle_key)
            for v in vehicles_here:
                dup = v.duplicated_count()
                mal = v.malformed_count()
                tags = []
                if dup > 0:
                    tags.append("duplicates")
                if mal > 0:
                    tags.append("malformed")
                disp = v.data.get("manufacturer", "").strip()
                if not disp:
                    disp = v.path.name
                item_id = self.vehicles_view.insert(
                    parent_item,
                    "end",
                    text=disp,
                    values=(dup, mal),
                    tags=tuple(tags)
                )
                self._node_map[item_id] = {"type": "vehicle", "path": v.path, "vehicle": v}
                self._vehicle_item_by_path[str(v.path)] = item_id

        add_children("", "")
        self.autosize_treeview(self.vehicles_view)

    def view_malformed(self):
        if not self.selected_vehicle:
            return

        malformed = []
        for code, desc in self.selected_vehicle.dtcs:
            if not code.strip() or not desc.strip():
                malformed.append((code, desc))

        if not malformed:
            messagebox.showinfo("Malformed DTCs", "No malformed DTC entries found.")
            return

        self.dtc_listbox.delete(0, tk.END)
        self.filtered_dtcs = malformed
        for code, desc in malformed:
            self.dtc_listbox.insert(tk.END, f"{code}\t{desc}")

    def view_duplicates(self):
        if not self.selected_vehicle:
            return

        counts = {}
        for code, _ in self.selected_vehicle.dtcs:
            counts[code] = counts.get(code, 0) + 1

        duplicates = []
        for code, desc in self.selected_vehicle.dtcs:
            if counts.get(code, 0) > 1:
                duplicates.append((code, desc))

        if not duplicates:
            messagebox.showinfo("Duplicates", "No duplicated DTCs found.")
            return

        self.dtc_listbox.delete(0, tk.END)
        self.filtered_dtcs = duplicates
        for code, desc in duplicates:
            self.dtc_listbox.insert(tk.END, f"{code}\t{desc}")

    def load_vehicles(self):
        self.vehicles.clear()
        root = self.getRootPath()
        if not root.exists():
            root.mkdir(parents=True, exist_ok=True)

        for desc_file in root.rglob("desc.ini"):
            vpath = desc_file.parent
            v = Vehicle(vpath)
            self.vehicles.append(v)

        self.selected_vehicle = None
        self.selected_folder = None
        self.clear_details()
        self.update_vehicle_filter()

    def update_vehicle_filter(self):
        prev_vehicle_path = str(self.selected_vehicle.path) if self.selected_vehicle else None
        prev_folder_path = str(self.selected_folder) if self.selected_folder else None

        self._render_tree(self.vehicles)

        if prev_vehicle_path and prev_vehicle_path in self._vehicle_item_by_path:
            item_id = self._vehicle_item_by_path[prev_vehicle_path]
            self.vehicles_view.selection_set(item_id)
            self.vehicles_view.see(item_id)
            self.on_vehicle_select(None)
            return

        if prev_folder_path:
            for iid, info in self._node_map.items():
                if info.get("type") == "folder" and str(info.get("path")) == prev_folder_path:
                    self.vehicles_view.selection_set(iid)
                    self.vehicles_view.see(iid)
                    self.on_vehicle_select(None)
                    return

        self.selected_vehicle = None
        self.selected_folder = None
        self.clear_details()
        self.autosize_treeview(self.vehicles_view)

    def on_vehicle_select(self, event):
        info = self._get_selected_item_info()
        if not info:
            return

        if info["type"] == "folder":
            self.selected_folder = info["path"]
            self.selected_vehicle = None
            self.clear_details()
            return

        if info["type"] == "vehicle":
            self.selected_folder = info["path"].parent
            self.selected_vehicle = info["vehicle"]
            self.show_vehicle_details()
            self.update_dtc_filter()
            return

    def clear_details(self):
        for ent in self.entries.values():
            ent.delete(0, tk.END)
        self.dtc_listbox.delete(0, tk.END)

    def show_vehicle_details(self):
        if not self.selected_vehicle:
            self.clear_details()
            return
        v = self.selected_vehicle
        for key, ent in self.entries.items():
            ent.delete(0, tk.END)
            ent.insert(0, v.data.get(key, ""))
        self.update_dtc_filter()

    def update_dtc_filter(self):
        self.dtc_listbox.delete(0, tk.END)
        self.filtered_dtcs = []
        if not self.selected_vehicle:
            return
        query = self.dtc_search_var.get().lower()
        for code, desc in self.selected_vehicle.dtcs:
            line = f"{code}\t{desc}"
            if query in code.lower() or query in desc.lower():
                self.filtered_dtcs.append((code, desc))
                self.dtc_listbox.insert(tk.END, line)

    def add_folder(self):
        base = self._get_selected_folder_path()
        rel_base = ""
        try:
            rel_base = str(base.relative_to(self.getRootPath())).replace("\\", "/").strip("/")
        except Exception:
            rel_base = ""

        prompt = "Enter new folder name (can be nested, e.g. citroen/900):"
        if rel_base:
            prompt += f"\n(under: {rel_base})"
        folder_name = simpledialog.askstring("Add Folder", prompt, parent=self)
        if not folder_name:
            return

        folder_name = folder_name.strip().strip("/").replace("\\", "/")
        if folder_name == "":
            return

        new_path = base / folder_name
        if new_path.exists():
            messagebox.showerror("Error", "Folder already exists.")
            return

        new_path.mkdir(parents=True, exist_ok=True)
        self.update_vehicle_filter()

        try:
            rel = str(new_path.relative_to(self.getRootPath())).replace("\\", "/").strip("/")
        except Exception:
            rel = ""
        if rel and rel in self._folder_item_by_rel:
            iid = self._folder_item_by_rel[rel]
            self.vehicles_view.selection_set(iid)
            self.vehicles_view.see(iid)
            self.on_vehicle_select(None)

    def rename_folder(self):
        info = self._get_selected_item_info()
        if not info or info["type"] != "folder":
            return

        src = info["path"]
        root = self.getRootPath()

        try:
            rel_src = str(src.relative_to(root)).replace("\\", "/").strip("/")
        except Exception:
            rel_src = src.name

        if (src / "desc.ini").exists():
            messagebox.showerror("Error", "Selected folder is a vehicle folder (has desc.ini). Use Move Vehicle instead.")
            return

        new_name = simpledialog.askstring("Rename Folder", "Enter new folder name:", initialvalue=src.name, parent=self)
        if not new_name:
            return

        new_name = new_name.strip().strip("/").replace("\\", "/")
        if "/" in new_name:
            messagebox.showerror("Error", "Folder rename must be a single name (no '/').")
            return

        dst = src.parent / new_name
        if dst.exists():
            messagebox.showerror("Error", "Destination folder already exists.")
            return

        src.rename(dst)
        self.selected_folder = dst
        self.load_vehicles()

    def delete_folder(self):
        info = self._get_selected_item_info()
        if not info or info["type"] != "folder":
            return

        p = info["path"]
        if (p / "desc.ini").exists():
            messagebox.showerror("Error", "Selected folder is a vehicle folder (has desc.ini). Use Delete Vehicle.")
            return

        if not messagebox.askyesno("Confirm", f"Delete folder '{p.name}' and ALL its contents?\nThis cannot be undone."):
            return

        shutil.rmtree(p)
        self.selected_folder = None
        self.selected_vehicle = None
        self.load_vehicles()

    def add_vehicle(self):
        base = self._get_selected_folder_path()
        root = self.getRootPath()

        folder_name = simpledialog.askstring(
            "Add Vehicle",
            "Enter new vehicle folder name (e.g. 900 or newvehicle):",
            parent=self
        )
        if not folder_name:
            return

        folder_name = folder_name.strip().strip("/").replace("\\", "/")
        if folder_name == "":
            return

        new_path = base / folder_name
        if new_path.exists():
            messagebox.showerror("Error", "Folder already exists.")
            return

        new_path.mkdir(parents=True, exist_ok=True)
        (new_path / "desc.ini").write_text("", encoding="utf-8")
        (new_path / "codes.tsv").write_text("", encoding="utf-8")

        self.load_vehicles()

        item_id = self._vehicle_item_by_path.get(str(new_path))
        if item_id:
            self.vehicles_view.selection_set(item_id)
            self.vehicles_view.see(item_id)
            self.on_vehicle_select(None)

    def move_vehicle(self):
        if not self.selected_vehicle:
            return

        root = self.getRootPath()
        src = self.selected_vehicle.path

        try:
            rel_src = str(src.relative_to(root)).replace("\\", "/")
        except Exception:
            rel_src = src.name

        dest_base = self._get_selected_folder_path()

        try:
            rel_dest_base = str(dest_base.relative_to(root)).replace("\\", "/").strip("/")
        except Exception:
            rel_dest_base = ""

        prompt = "Move selected vehicle folder into which destination folder (relative to root)?\nExample: citroen/900"
        if rel_dest_base:
            prompt += f"\n(default: {rel_dest_base})"

        dest_rel = simpledialog.askstring("Move Vehicle", prompt, parent=self)
        if dest_rel is None:
            return

        dest_rel = dest_rel.strip().replace("\\", "/").strip("/")
        if dest_rel == "":
            dest_folder = root
        else:
            dest_folder = root / dest_rel

        if not dest_folder.exists():
            if not messagebox.askyesno("Create Folder", "Destination folder does not exist. Create it?"):
                return
            dest_folder.mkdir(parents=True, exist_ok=True)

        dst = dest_folder / src.name
        if dst.exists():
            messagebox.showerror("Error", "Destination already contains a folder with the same name.")
            return

        src.rename(dst)
        self.selected_vehicle = None
        self.selected_folder = dst.parent
        self.load_vehicles()

        item_id = self._vehicle_item_by_path.get(str(dst))
        if item_id:
            self.vehicles_view.selection_set(item_id)
            self.vehicles_view.see(item_id)
            self.on_vehicle_select(None)

    def delete_vehicle(self):
        if not self.selected_vehicle:
            return
        if not messagebox.askyesno(
            "Confirm",
            f"Delete vehicle folder '{self.selected_vehicle.path.name}'?\nThis cannot be undone."
        ):
            return
        shutil.rmtree(self.selected_vehicle.path)
        self.selected_vehicle = None
        self.load_vehicles()

    def import_dtc(self):
        if not self.selected_vehicle:
            messagebox.showwarning("No Vehicle Selected", "Please select a vehicle first.")
            return
        file_path = filedialog.askopenfilename(
            title="Select DTC File to Import",
            filetypes=[("TSV Files", "*.tsv")]
        )
        if not file_path:
            return
        try:
            new_dtcs = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        new_dtcs.append((parts[0], parts[1]))
                    else:
                        new_dtcs.append((parts[0], ""))
            existing_set = set(tuple(dtc) for dtc in self.selected_vehicle.dtcs)
            for dtc in new_dtcs:
                if dtc not in existing_set:
                    self.selected_vehicle.dtcs.append(dtc)
            self.update_dtc_filter()
            messagebox.showinfo("Import Complete", f"Imported {len(new_dtcs)} DTC(s) from file.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import DTCs:\n{e}")

    def import_dtc_csv(self):
        if not self.selected_vehicle:
            messagebox.showwarning("No Vehicle Selected", "Please select a vehicle first.")
            return
        file_path = filedialog.askopenfilename(
            title="Select DTC CSV File to Import",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not file_path:
            return
        try:
            new_dtcs = []
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = (row.get("code") or "").strip()
                    desc = (row.get("description") or "").strip()
                    if code:
                        new_dtcs.append((code, desc))
            existing_set = set(tuple(dtc) for dtc in self.selected_vehicle.dtcs)
            for dtc in new_dtcs:
                if dtc not in existing_set:
                    self.selected_vehicle.dtcs.append(dtc)
            self.update_dtc_filter()
            messagebox.showinfo("Import Complete", f"Imported {len(new_dtcs)} DTC(s) from file.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import DTCs:\n{e}")

    def import_dtc_json(self):
        if not self.selected_vehicle:
            messagebox.showwarning("No Vehicle Selected", "Please select a vehicle first.")
            return
        file_path = filedialog.askopenfilename(
            title="Select DTC JSON File to Import",
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_path:
            return
        try:
            new_dtcs = []
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "code" in item:
                            code = str(item.get("code", "")).strip()
                            desc = str(item.get("description", "")).strip()
                            if code:
                                new_dtcs.append((code, desc))
            existing_set = set(tuple(dtc) for dtc in self.selected_vehicle.dtcs)
            for dtc in new_dtcs:
                if dtc not in existing_set:
                    self.selected_vehicle.dtcs.append(dtc)
            self.update_dtc_filter()
            messagebox.showinfo("Import Complete", f"Imported {len(new_dtcs)} DTC(s) from file.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import DTCs:\n{e}")

    def add_dtc(self):
        if not self.selected_vehicle:
            return
        code = simpledialog.askstring("Add DTC", "Enter DTC code:", parent=self)
        if not code:
            return
        desc = simpledialog.askstring("Add DTC", "Enter DTC description:", parent=self)
        if desc is None:
            return
        self.selected_vehicle.dtcs.append((code, desc))
        self.update_dtc_filter()

    def edit_dtc(self):
        if not self.selected_vehicle:
            return
        sel = self.dtc_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        old_code, old_desc = self.filtered_dtcs[idx]
        code = simpledialog.askstring("Edit DTC", "Edit DTC code:", initialvalue=old_code, parent=self)
        if not code:
            return
        desc = simpledialog.askstring("Edit DTC", "Edit DTC description:", initialvalue=old_desc, parent=self)
        if desc is None:
            return
        for i, (c, d) in enumerate(self.selected_vehicle.dtcs):
            if c == old_code and d == old_desc:
                self.selected_vehicle.dtcs[i] = (code, desc)
                break
        self.update_dtc_filter()

    def remove_exact_duplicates(self):
        if not self.selected_vehicle:
            return

        counts = {}
        for code, desc in self.selected_vehicle.dtcs:
            counts[(code, desc)] = counts.get((code, desc), 0) + 1

        new_dtcs = []
        seen = set()
        for code, desc in self.selected_vehicle.dtcs:
            if counts[(code, desc)] > 1:
                if (code, desc) not in seen:
                    new_dtcs.append((code, desc))
                    seen.add((code, desc))
            else:
                new_dtcs.append((code, desc))

        self.selected_vehicle.dtcs = new_dtcs
        self.update_dtc_filter()
        messagebox.showinfo("Remove Exact Duplicates", "Exact duplicate DTC entries removed.")

    def remove_dtc(self):
        if not self.selected_vehicle:
            return
        sel = self.dtc_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        old_code, old_desc = self.filtered_dtcs[idx]
        for i, (c, d) in enumerate(self.selected_vehicle.dtcs):
            if c == old_code and d == old_desc:
                del self.selected_vehicle.dtcs[i]
                break
        self.update_dtc_filter()

    def save_changes(self):
        for v in self.vehicles:
            if v is self.selected_vehicle:
                for key, ent in self.entries.items():
                    val = ent.get().strip()
                    if val:
                        v.data[key] = val
                    else:
                        v.data.pop(key, None)
            v.save()
        messagebox.showinfo("Saved", "All vehicles saved to disk.")

    def reload_from_fs(self):
        if messagebox.askyesno("Reload", "Discard all unsaved changes and reload from disk?"):
            self.load_vehicles()
