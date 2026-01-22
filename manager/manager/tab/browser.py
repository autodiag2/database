import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
import configparser
import os

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
            # Use empty section to parse ini without sections
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
        # Write desc.ini omitting empty properties
        lines = []
        for key in ("manufacturer", "engine", "ecu", "years"):
            v = self.data.get(key, "").strip()
            if v:
                lines.append(f"{key}={v}")
        with open(self.desc_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        # Write codes.tsv
        with open(self.codes_path, "w", encoding="utf-8") as f:
            for code, desc in self.dtcs:
                f.write(f"{code}\t{desc}\n")

class BrowserTab(tk.Frame):

    def getRootPath(self):
        return Path(self.data_entry.get()) / "vehicle"
    
    def __init__(self, parent, data_entry: tk.Entry):
        super().__init__(parent)

        self.data_entry = data_entry
        self.vehicles = []  # list of Vehicle
        self.selected_vehicle = None

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

        # Left: Vehicle list
        self.vehicle_listbox = tk.Listbox(self.scroll_frame, height=20, width=30)
        self.vehicle_listbox.grid(row=0, column=0, rowspan=10, sticky="nswe", padx=5, pady=5)
        self.vehicle_listbox.bind("<<ListboxSelect>>", self.on_vehicle_select)

        # Buttons for vehicle management
        btn_frame = tk.Frame(self.scroll_frame)
        btn_frame.grid(row=10, column=0, sticky="we", padx=5, pady=5)
        tk.Button(btn_frame, text="Add Vehicle", command=self.add_vehicle).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Delete Vehicle", command=self.delete_vehicle).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Reload", command=self.load_vehicles).pack(side="left", padx=3)
        tk.Button(btn_frame, text="Save Changes", command=self.save_changes).pack(side="left", padx=3)

        # Right: Vehicle details & DTC editor
        details_frame = tk.LabelFrame(self.scroll_frame, text="Vehicle Details")
        details_frame.grid(row=0, column=1, sticky="nwe", padx=5, pady=5)

        # Vehicle properties entries
        self.entries = {}
        for i, key in enumerate(["manufacturer", "engine", "ecu", "years"]):
            tk.Label(details_frame, text=key.capitalize()+":").grid(row=i, column=0, sticky="e", padx=2, pady=2)
            ent = tk.Entry(details_frame, width=40)
            ent.grid(row=i, column=1, sticky="we", padx=2, pady=2)
            self.entries[key] = ent

        # DTC listbox + buttons
        dtc_frame = tk.LabelFrame(self.scroll_frame, text="DTC List")
        dtc_frame.grid(row=1, column=1, sticky="nswe", padx=5, pady=5)

        self.dtc_listbox = tk.Listbox(dtc_frame, height=15, width=50)
        self.dtc_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        dtc_btn_frame = tk.Frame(dtc_frame)
        dtc_btn_frame.pack(side="right", fill="y", padx=5)

        tk.Button(dtc_btn_frame, text="Add DTC", command=self.add_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Edit DTC", command=self.edit_dtc).pack(fill="x", pady=2)
        tk.Button(dtc_btn_frame, text="Remove DTC", command=self.remove_dtc).pack(fill="x", pady=2)

        self.load_vehicles()

    def load_vehicles(self):
        self.vehicles.clear()
        self.vehicle_listbox.delete(0, tk.END)

        # Search for desc.ini recursively inside root_path
        for desc_file in self.getRootPath().rglob("desc.ini"):
            vpath = desc_file.parent
            self.vehicles.append(Vehicle(vpath))

        self.vehicles.sort(key=lambda v: v.data.get("manufacturer", "").lower())
        for v in self.vehicles:
            name = v.data.get("manufacturer", v.path.name)
            self.vehicle_listbox.insert(tk.END, name)
        self.selected_vehicle = None
        self.clear_details()

    def on_vehicle_select(self, _):
        sel = self.vehicle_listbox.curselection()
        if not sel:
            self.selected_vehicle = None
            self.clear_details()
            return
        index = sel[0]
        self.selected_vehicle = self.vehicles[index]
        self.show_vehicle_details()

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
        self.refresh_dtcs()

    def refresh_dtcs(self):
        self.dtc_listbox.delete(0, tk.END)
        if not self.selected_vehicle:
            return
        for code, desc in self.selected_vehicle.dtcs:
            self.dtc_listbox.insert(tk.END, f"{code}\t{desc}")

    def add_vehicle(self):
        # Ask for new folder name
        folder_name = simpledialog.askstring("Add Vehicle", "Enter new vehicle folder name (e.g. newvehicle):", parent=self)
        if not folder_name:
            return
        new_path = self.getRootPath() / folder_name
        if new_path.exists():
            messagebox.showerror("Error", "Folder already exists.")
            return
        new_path.mkdir(parents=True)
        # Create empty desc.ini and codes.tsv
        (new_path / "desc.ini").write_text("", encoding="utf-8")
        (new_path / "codes.tsv").write_text("", encoding="utf-8")
        self.load_vehicles()
        # Select newly added vehicle
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

    def add_dtc(self):
        if not self.selected_vehicle:
            return
        code = simpledialog.askstring("Add DTC", "Enter DTC code:", parent=self)
        if not code:
            return
        desc = simpledialog.askstring("Add DTC", "Enter DTC description:", parent=self) or ""
        self.selected_vehicle.dtcs.append((code, desc))
        self.refresh_dtcs()

    def edit_dtc(self):
        if not self.selected_vehicle:
            return
        sel = self.dtc_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        old_code, old_desc = self.selected_vehicle.dtcs[idx]
        code = simpledialog.askstring("Edit DTC", "Edit DTC code:", initialvalue=old_code, parent=self)
        if not code:
            return
        desc = simpledialog.askstring("Edit DTC", "Edit DTC description:", initialvalue=old_desc, parent=self) or ""
        self.selected_vehicle.dtcs[idx] = (code, desc)
        self.refresh_dtcs()

    def remove_dtc(self):
        if not self.selected_vehicle:
            return
        sel = self.dtc_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        del self.selected_vehicle.dtcs[idx]
        self.refresh_dtcs()

    def save_changes(self):
        if not self.selected_vehicle:
            return
        for key, ent in self.entries.items():
            val = ent.get().strip()
            if val:
                self.selected_vehicle.data[key] = val
            else:
                self.selected_vehicle.data.pop(key, None)
        self.selected_vehicle.save()
        messagebox.showinfo("Saved", "Changes saved to disk.")

    def reload_from_fs(self):
        self.load_vehicles()