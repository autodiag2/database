import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
import configparser
import os
import re

class Vehicle:
    def __init__(self, path: Path):
        self.path = path
        self.desc_path = path / "desc.ini"
        self.codes_path = path / "codes.tsv"
        self.data = {}  # keys: manufacturer, engine, ecu, years
        self.dtcs = []  # list of (code, description)
        self.load()

    def load(self):
        self.data.clear()
        self.dtcs.clear()
        if self.desc_path.exists():
            cfg = configparser.ConfigParser()
            with open(self.desc_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = "[vehicle]\n" + content
            cfg.read_string(content)
            for key in ("manufacturer", "engine", "ecu", "years"):
                val = cfg.get("vehicle", key, fallback=None)
                if val:
                    self.data[key] = val

        if self.codes_path.exists():
            with open(self.codes_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split("\t", 1)
                        if len(parts) == 2:
                            self.dtcs.append(parts)
                        else:
                            self.dtcs.append((parts[0], ""))

    def save(self):
        lines = []
        for key in ("manufacturer", "engine", "ecu", "years"):
            v = self.data.get(key, "").strip()
            if v:
                lines.append(f"{key}={v}")
        with open(self.desc_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        with open(self.codes_path, "w", encoding="utf-8") as f:
            for code, desc in sorted(self.dtcs, key=lambda x: x[0]):
                f.write(f"{code}\t{desc}\n")

class BrowserTab(tk.Frame):

    def getRootPath(self):
        return Path(self.data_entry.get()) / "vehicle"
    
    def __init__(self, parent, data_entry: tk.Entry):
        super().__init__(parent)

        self.data_entry = data_entry
        self.vehicles = []
        self.selected_vehicle = None
        self.filtered_vehicles = []  # For vehicle search filter
        self.filtered_dtcs = []      # For dtc search filter

        # Scrollable frame setup
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
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Vehicle search
        tk.Label(self.scroll_frame, text="Search Vehicles:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vehicle_search_var = tk.StringVar()
        self.vehicle_search_var.trace_add("write", lambda *a: self.update_vehicle_filter())
        self.vehicle_search_entry = tk.Entry(self.scroll_frame, textvariable=self.vehicle_search_var)
        self.vehicle_search_entry.grid(row=1, column=0, sticky="we", padx=5)

        # Left: Vehicle listbox
        self.vehicle_listbox = tk.Listbox(self.scroll_frame, height=15, width=30)
        self.vehicle_listbox.grid(row=2, column=0, rowspan=9, sticky="nswe", padx=5, pady=5)
        self.vehicle_listbox.bind("<<ListboxSelect>>", self.on_vehicle_select)

        # Vehicle buttons
        btn_frame = tk.Frame(self.scroll_frame)
        btn_frame.grid(row=11, column=0, sticky="we", padx=5, pady=5)
        tk.Button(btn_frame, text="Add Vehicle", command=self.add_vehicle).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Delete Vehicle", command=self.delete_vehicle).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Reload", command=self.load_vehicles).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Save Changes", command=self.save_changes).pack(side="left", padx=3)

        # Right: Vehicle details frame
        details_frame = tk.LabelFrame(self.scroll_frame, text="Vehicle Details")
        details_frame.grid(row=0, column=1, sticky="nwe", rowspan=5, padx=5, pady=5)

        self.entries = {}
        for i, key in enumerate(["manufacturer", "engine", "ecu", "years"]):
            tk.Label(details_frame, text=key.capitalize() + ":").grid(row=i, column=0, sticky="e", padx=2, pady=2)
            ent = tk.Entry(details_frame, width=40)
            ent.grid(row=i, column=1, sticky="we", padx=2, pady=2)
            self.entries[key] = ent

        # DTC search
        tk.Label(self.scroll_frame, text="Search DTCs:").grid(row=5, column=1, sticky="w", padx=5, pady=2)
        self.dtc_search_var = tk.StringVar()
        self.dtc_search_var.trace_add("write", lambda *a: self.update_dtc_filter())
        self.dtc_search_entry = tk.Entry(self.scroll_frame, textvariable=self.dtc_search_var)
        self.dtc_search_entry.grid(row=6, column=1, sticky="we", padx=5)

        # DTC listbox + buttons
        dtc_frame = tk.LabelFrame(self.scroll_frame, text="DTC List")
        dtc_frame.grid(row=7, column=1, sticky="nswe", rowspan=5, padx=5, pady=5)

        self.dtc_listbox = tk.Listbox(dtc_frame, height=15, width=50)
        self.dtc_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.dtc_listbox.bind("<Double-Button-1>", lambda e: self.edit_dtc())

        dtc_btn_frame = tk.Frame(dtc_frame)
        dtc_btn_frame.pack(side="right", fill="y", padx=5)

        tk.Button(dtc_btn_frame, text="Add DTC", command=self.add_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Edit DTC", command=self.edit_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Remove DTC", command=self.remove_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Import DTC", command=self.import_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="View Duplicates", command=self.view_duplicates).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="View Malformed", command=self.view_malformed).pack(fill="x", pady=2)

        self.load_vehicles()

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
        self.vehicle_listbox.delete(0, tk.END)

        for desc_file in self.getRootPath().rglob("desc.ini"):
            vpath = desc_file.parent
            self.vehicles.append(Vehicle(vpath))

        self.vehicles.sort(key=lambda v: v.data.get("manufacturer", "").lower())
        self.update_vehicle_filter()
        self.selected_vehicle = None
        self.clear_details()

    def update_vehicle_filter(self):
        query = self.vehicle_search_var.get().lower()
        self.vehicle_listbox.delete(0, tk.END)
        self.filtered_vehicles = []
        for v in self.vehicles:
            name = v.data.get("manufacturer", v.path.name)
            if query in name.lower():
                self.filtered_vehicles.append(v)
                self.vehicle_listbox.insert(tk.END, name)
        self.selected_vehicle = None
        self.clear_details()

    def on_vehicle_select(self, _):
        sel = self.vehicle_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        self.selected_vehicle = self.filtered_vehicles[index]
        self.show_vehicle_details()
        self.update_dtc_filter()

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

    def add_vehicle(self):
        folder_name = simpledialog.askstring("Add Vehicle", "Enter new vehicle folder name (e.g. newvehicle):", parent=self)
        if not folder_name:
            return
        new_path = self.getRootPath() / folder_name
        if new_path.exists():
            messagebox.showerror("Error", "Folder already exists.")
            return
        new_path.mkdir(parents=True)
        (new_path / "desc.ini").write_text("", encoding="utf-8")
        (new_path / "codes.tsv").write_text("", encoding="utf-8")
        self.load_vehicles()
        for i, v in enumerate(self.vehicles):
            if v.path == new_path:
                self.vehicle_listbox.selection_clear(0, tk.END)
                self.vehicle_listbox.selection_set(i)
                self.vehicle_listbox.see(i)
                self.on_vehicle_select(None)
                break

    def delete_vehicle(self):
        if not self.selected_vehicle:
            return
        if not messagebox.askyesno("Confirm", f"Delete vehicle folder '{self.selected_vehicle.path.name}'? This cannot be undone."):
            return
        import shutil
        shutil.rmtree(self.selected_vehicle.path)
        self.load_vehicles()

    def import_dtc(self):
        if not self.selected_vehicle:
            messagebox.showwarning("No Vehicle Selected", "Please select a vehicle first.")
            return
        file_path = filedialog.askopenfilename(
            title="Select DTC File to Import",
            filetypes=[("TSV Files", "*.tsv"), ("Text Files", "*.txt"), ("All Files", "*.*")]
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
            # Merge, avoiding duplicates (by code and description)
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
        # Update in original dtcs list (not filtered)
        for i, (c, d) in enumerate(self.selected_vehicle.dtcs):
            if c == old_code and d == old_desc:
                self.selected_vehicle.dtcs[i] = (code, desc)
                break
        self.update_dtc_filter()

    def remove_dtc(self):
        if not self.selected_vehicle:
            return
        sel = self.dtc_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        old_code, old_desc = self.filtered_dtcs[idx]
        # Remove from original dtcs list (not filtered)
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
