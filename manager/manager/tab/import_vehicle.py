import manager.tk.tk as tk
from manager.tab.import_tab import ImportTab
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
import re
import io
import yaml
import unicodedata

def slug(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9_.-]", "_", text)
    return text

def current_timestamp():
    return datetime.now(
        ZoneInfo("Europe/Paris")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")

def normalize_text(value):
    if not isinstance(value, str):
        return value

    value = unicodedata.normalize("NFKC", value)

    return (
        value
        .replace("\u2019", "'")  # right single quotation mark
        .replace("\u2018", "'")  # left single quotation mark
        .replace("\u02BC", "'")  # modifier letter apostrophe
        .replace("\u0060", "'")  # grave accent
        .replace("\u00B4", "'")  # acute accent
        .lower()
    )

# Type,Brand,Model,Year,Version,Engine,Engine_type,Fuel,Power_PS,Power,Ecu_maker,MCU_Type,MCU,Ecu_model,Connection_mode
# Car,Abarth,124 Spider,2008-2017,348,1400 MultiAir,55253268,Petrol,170,0,MARELLI,ECM,SPC564A80,8GMK,"BOOT, OBD"
class ImportVehicleTab(ImportTab):

    def __init__(self, parent, plain_path_var):
        super().__init__(parent, plain_path_var)

        self._build_configuration()
        self._build_input()
        self._build_buttons()
        self._add_log_widget()

    def _build_configuration(self):
        frame = tk.LabelFrame(
            self.left_pane,
            text="Import configuration"
        )
        frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        tk.Label(
            frame,
            text="Evidence source:"
        ).grid(
            row=0,
            column=0,
            sticky="e",
            padx=5,
            pady=3
        )

        self.evidence_var = tk.StringVar()

        tk.Entry(
            frame,
            textvariable=self.evidence_var,
            width=60
        ).grid(
            row=0,
            column=1,
            sticky="we",
            padx=5,
            pady=3
        )
        self.evidence_var.set("https://dev-srv.tlkeys.com/storage/files/pcmtuner/pcmtuner-detail-car-ecu-list.pdf")

        frame.columnconfigure(
            1,
            weight=1
        )

    def _build_input(self):
        frame = tk.LabelFrame(
            self.left_pane,
            text="CSV data"
        )
        frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        self.input_text = tk.Text(
            frame,
            wrap="none",
            height=18
        )
        self.input_text.insert(
            "1.0",
            """
Type,Brand,Model,Year,Version,Engine,Engine_type,Fuel,Power_PS,Power,Ecu_maker,MCU_Type,MCU,Ecu_model,Connection_mode
Car,Abarth,124 Spider,2008-2017,348,1400 MultiAir,55253268,Petrol,170,0,MARELLI,ECM,SPC564A80,8GMK,"BOOT, OBD"
Car,Abarth,500,2008-2018,312,1400 Fire TJET 595 Turismo,312.A1.000,Petrol,160,118,Bosch,ECM,TC1724,ME17.3.0,"BENCH, BOOT"
Car,Abarth,500,2008-2018,312,1400 Fire TJET 595 Turismo,312.A3.000,Petrol,160,118,Bosch,ECM,TC1724,ME17.3.0,"BENCH, BOOT"
Car,Abarth,500,2008-2018,312,1400 Fire TJET 695 Biposto,312.A9.000,Petrol,190,139,Bosch,ECM,TC1724,ME17.3.0,"BENCH, BOOT"
            """
        )

        scroll_y = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.input_text.yview
        )

        scroll_x = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=self.input_text.xview
        )

        self.input_text.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.input_text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scroll_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scroll_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        frame.rowconfigure(
            0,
            weight=1
        )

        frame.columnconfigure(
            0,
            weight=1
        )

    def _build_buttons(self):
        frame = tk.Frame(self.left_pane)
        frame.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        tk.Button(
            frame,
            text="Copy",
            command=self.on_copy
        ).pack(side="left")

        tk.Button(
            frame,
            text="Paste",
            command=self.on_paste
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            frame,
            text="Clear",
            command=self.on_clear
        ).pack(
            side="left",
            padx=5
        )

        ttk.Separator(
            frame,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=10
        )

        tk.Button(
            frame,
            text="Import",
            command=self.on_import
        ).pack(side="left")

    def on_copy(self):
        text = self.input_text.get(
            "1.0",
            "end-1c"
        )

        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def on_paste(self):
        try:
            text = self.root.clipboard_get()
        except Exception:
            return

        self.input_text.insert(
            "insert",
            text
        )

    def on_clear(self):
        self.input_text.delete(
            "1.0",
            "end"
        )

    def guess_manufacturer_from_mcu_model(self, model: str) -> str:
        model = (model or "").upper()

        prefixes = {
            "TC": "infineon",
            "SAK": "infineon",
            "C16": "infineon",
            "XC": "infineon",

            "MPC": "nxp",
            "MC9": "nxp",
            "MK": "nxp",
            "S12": "nxp",

            "SPC": "stmicroelectronics",
            "ST10": "stmicroelectronics",
            "STM": "stmicroelectronics",

            "RH850": "renesas",
            "R7F": "renesas",
            "V850": "renesas",
            "76F": "nec",
            "D76F": "nec",
            "SH": "renesas",

            "TMS": "ti",
            "AM": "ti",
        }

        for prefix, manufacturer in prefixes.items():
            if model.startswith(prefix):
                return manufacturer

        return "generic"

    def import_mcu(self, MCU: str) -> str | None:

        MCU = (MCU or "").strip()

        if MCU == "":
            return None

        manufacturer = self.guess_manufacturer_from_mcu_model(MCU)
        mcu_ref = f"{manufacturer}/{MCU}"

        manufacturer_path = (
            self.get_data_src() /
            "mcu" /
            manufacturer
        )

        manufacturer_path.mkdir(
            parents=True,
            exist_ok=True
        )

        manufacturer_def = manufacturer_path / "def.yml"

        if not manufacturer_def.exists():

            self.write_yaml(manufacturer_def, {
                "manufacturer": manufacturer
            })

        mcu_path = manufacturer_path / slug(MCU)
        mcu_path.mkdir(exist_ok=True)

        yaml_path = mcu_path / "def.yml"

        if yaml_path.exists():

            data = self.read_yaml(yaml_path)

            new_file = False

        else:

            data = {
                "created": current_timestamp(),
                "updated": current_timestamp(),
                "model": MCU,
                "evidence": []
            }

            new_file = True

        changed = new_file
        conflict = False
        if data.get("model") != MCU:
            conflict = True
            changed |= self.add_conflict(
                yaml_path,
                data,
                "model",
                MCU
            )

            return mcu_ref



        evidences = data.setdefault("evidence", [])

        if not conflict:
            evidence = self.get_evidence_input()

            if evidence and evidence not in evidences:
                evidences.append(evidence)
                changed = True

        if changed:

            data["updated"] = current_timestamp()
            self.write_yaml(yaml_path, data)
            if new_file:
                self.log(f"Created MCU: {mcu_ref}")
            else:
                self.log(f"Updated MCU: {mcu_ref}")
        else:
            self.log(f"MCU unchanged: {manufacturer}/{MCU}")

        return mcu_ref
    
    def read_yaml(self, path):
        """
        Read a YAML file. Returns {} if the file does not exist or is empty.
        """
        path = Path(path)

        if not path.exists():
            return {}

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data or {}


    def write_yaml(self, path, data):
        """
        Write a YAML file, creating parent directories if needed.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )

    def insert_or_conflict(self, yaml_path, data, field, value):
        changed = False
        conflict = False

        if value is None or value == "":
            return changed, conflict

        current = data.get(field)

        if current is not None and current != "":
            if isinstance(current, str) and isinstance(value, str):
                if normalize_text(current) != normalize_text(value):
                    conflict = True
                    changed |= self.add_conflict(
                        yaml_path,
                        data,
                        field,
                        value
                    )
                elif current != value:
                    data[field] = value
                    changed = True
            else:
                if current != value:
                    conflict = True
                    changed |= self.add_conflict(
                        yaml_path,
                        data,
                        field,
                        value
                    )
        else:
            data[field] = value
            changed = True

        return changed, conflict
    
    def import_ecu(self, Ecu_maker, Ecu_model, ECU_type="ECM", MCU=""):
        Ecu_maker = (Ecu_maker or "").strip()
        Ecu_model = (Ecu_model or "").strip()
        ECU_type = (ECU_type or "ECM").strip()
        MCU = (MCU or "").strip()

        if not Ecu_maker or not Ecu_model:
            return None

        maker_dir = self.get_data_src() / "ecu" / slug(Ecu_maker)
        maker_dir.mkdir(parents=True, exist_ok=True)

        maker_def = maker_dir / "def.yml"
        if not maker_def.exists():
            self.write_yaml(
                maker_def,
                {
                    "name": Ecu_maker,
                    "created": current_timestamp(),
                    "updated": current_timestamp(),
                },
            )

        ecu_dir = maker_dir / slug(Ecu_model)
        ecu_dir.mkdir(parents=True, exist_ok=True)

        ecu_def = ecu_dir / "def.yml"

        changed = False
        if ecu_def.exists():
            data = self.read_yaml(ecu_def)
        else:
            changed = True
            data = {
                "model": Ecu_model,
                "created": current_timestamp(),
            }
        
        conflict = False
        changed_rv, conflict_rv = self.insert_or_conflict(ecu_def, data, "model", Ecu_model)
        changed |= changed_rv
        conflict |= conflict_rv
        changed_rv, conflict_rv = self.insert_or_conflict(ecu_def, data, "type", ECU_type)
        changed |= changed_rv
        conflict |= conflict_rv

        mcu_ref = self.import_mcu(MCU)

        changed_rv, conflict_rv = self.insert_or_conflict(ecu_def, data, "mcu", mcu_ref)
        changed |= changed_rv
        conflict |= conflict_rv

        evidences = set(data.get("evidence", []))

        if data.get("type"):
            data["type"] = data["type"].upper()

        if not conflict:
            evidence = self.get_evidence_input()
            if evidence and evidence not in evidences:
                evidences.add(evidence)
                data["evidence"] = sorted(evidences)
                changed = True

        if changed:
            data["updated"] = current_timestamp()
            self.write_yaml(ecu_def, data)
            self.log(f"Imported ECU {Ecu_maker}/{Ecu_model}")
        else:
            self.log(f"ECU unchanged {Ecu_maker}/{Ecu_model}")

        return f"{Ecu_maker}/{Ecu_model}"

    def get_evidence_input(self):
        return self.evidence_var.get().strip()

    def add_conflict(self, yaml_path, yaml_data, field_name, value_to_store):
        self.log(
            f"Conflict on {yaml_path} "
            f"field '{field_name}': "
            f"stored={yaml_data.get(field_name)!r} "
            f"incoming={value_to_store!r}"
        )

        conflicts = yaml_data.setdefault("conflicts", {})
        field_conflicts = conflicts.setdefault(field_name, [])

        conflict = {
            "value": value_to_store,
            "evidence": self.get_evidence_input(),
        }

        need_add = conflict not in field_conflicts
        if need_add:
            field_conflicts.append(conflict)
        return need_add

    def insert_ecu(
        self,
        yaml_path,
        data,
        value
    ):
        changed = False
        conflict = False

        if not value:
            return changed, conflict

        ecus = data.get("ecu")

        if not ecus:
            data["ecu"] = [value]
            changed = True
            return changed, conflict

        if type([]) != type(ecus):
            print("invalid type for ecu")
            return changed, conflict

        if value in ecus:
            return changed, conflict

        # We do not rise conflict since there is low changes to encounter one
        ecus.append(value)
        changed = True

        return changed, conflict

    def import_vehicle(
        self,
        Type,
        Brand,
        Model,
        Year,
        Version,
        Power_KW,
        ecu_relative_path,
        engine_relative_path
    ):
        Type = (Type or "").strip()
        Brand = (Brand or "").strip()
        Model = (Model or "").strip()
        Year = (Year or "").strip()
        Version = (Version or "").strip()

        if not Brand or not Model:
            return None

        manufacturer_dir = (
            self.get_data_src() /
            "vehicle" /
            slug(Brand)
        )

        manufacturer_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        manufacturer_def = manufacturer_dir / "def.yml"

        if not manufacturer_def.exists():
            self.write_yaml(
                manufacturer_def,
                {
                    "manufacturer": Brand,
                },
            )

        vehicle_ref = f"{slug(Brand)}/{slug(Model)}"

        vehicle_dir = manufacturer_dir / slug(Model)
        vehicle_dir.mkdir(exist_ok=True)

        vehicle_def = vehicle_dir / "def.yml"

        if vehicle_def.exists():
            data = self.read_yaml(vehicle_def)
            new_file = False
        else:
            data = {
                "created": current_timestamp(),
                "model": Model,
                "type": Type.lower() if Type else "car",
                "evidence": [],
            }
            new_file = True

        changed = new_file
        conflict = False

        changed_rv, conflict_rv = self.insert_or_conflict(
            vehicle_def,
            data,
            "model",
            Model
        )
        changed |= changed_rv
        conflict |= conflict_rv

        changed_rv, conflict_rv = self.insert_or_conflict(
            vehicle_def,
            data,
            "type",
            Type.lower() if Type else "car"
        )
        changed |= changed_rv
        conflict |= conflict_rv

        evidences = data.setdefault("evidence", [])

        if not conflict:
            evidence = self.get_evidence_input()
            if evidence and evidence not in evidences:
                evidences.append(evidence)
                changed = True

        if changed:
            data["updated"] = current_timestamp()
            self.write_yaml(vehicle_def, data)

        versions_dir = vehicle_dir / "versions"
        versions_dir.mkdir(exist_ok=True)

        version_name = slug(Version) if Version else "generic"

        version_dir = versions_dir / version_name
        version_dir.mkdir(exist_ok=True)

        engine_slug = (
            slug(engine_relative_path.split("/")[-1])
            if engine_relative_path else
            "generic"
        )

        ecu_slug = (
            slug(ecu_relative_path.split("/")[-1])
            if ecu_relative_path else
            "generic"
        )

        variant_file = version_dir / f"{engine_slug}_{ecu_slug}.yml"

        if variant_file.exists():
            variant = self.read_yaml(variant_file)
            new_variant = False
        else:
            variant = {
                "created": current_timestamp(),
            }
            new_variant = True

        changed = new_variant
        conflict = False

        for field, value in (
            ("year", Year),
            ("version", Version),
            ("engine", engine_relative_path),
            ("power_kw", float(Power_KW) if Power_KW else None),
        ):
            if value not in (None, ""):
                changed_rv, conflict_rv = self.insert_or_conflict(
                    variant_file,
                    variant,
                    field,
                    value
                )
                changed |= changed_rv
                conflict |= conflict_rv

        changed_rv, conflict_rv = self.insert_ecu(
            variant_file,
            variant,
            ecu_relative_path
        )
        changed |= changed_rv
        conflict |= conflict_rv

        evidences = variant.setdefault("evidence", [])

        if not conflict:
            evidence = self.get_evidence_input()
            if evidence and evidence not in evidences:
                evidences.append(evidence)
                changed = True

        if changed:
            variant["updated"] = current_timestamp()
            self.write_yaml(variant_file, variant)

        if new_file:
            self.log(f"Created Vehicle: {vehicle_ref}")
        elif changed:
            self.log(f"Updated Vehicle: {vehicle_ref}")
        else:
            self.log(f"Vehicle unchanged: {vehicle_ref}")

        return vehicle_ref

    def import_engine(
        self,
        manufacturer,
        Engine,
        Engine_type="",
        Fuel=""
    ):
        manufacturer = (manufacturer or "").strip()
        Engine = (Engine or "").strip()
        Engine_type = (Engine_type or "").strip()
        Fuel = (Fuel or "").strip()

        if not manufacturer or not Engine:
            return None

        engine_code = Engine_type if Engine_type else Engine

        manufacturer_dir = (
            self.get_data_src() /
            "engine" /
            slug(manufacturer)
        )

        manufacturer_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        manufacturer_def = manufacturer_dir / "def.yml"

        if not manufacturer_def.exists():
            self.write_yaml(
                manufacturer_def,
                {
                    "manufacturer": manufacturer
                }
            )

        engine_ref = f"{manufacturer}/{engine_code}"

        engine_dir = manufacturer_dir / slug(engine_code)
        engine_dir.mkdir(exist_ok=True)

        yaml_path = engine_dir / "def.yml"

        if yaml_path.exists():
            data = self.read_yaml(yaml_path)
            new_file = False
        else:
            data = {
                "created": current_timestamp(),
                "name": [Engine],
                "code": engine_code,
                "evidence": [],
            }
            new_file = True

        changed = new_file
        conflict = False

        names = data.get("name", [])

        if isinstance(names, str):
            names = [names]
            data["name"] = names

        if Engine and Engine.lower() not in [name.lower() for name in names]:
            names.append(Engine)
            changed = True

        changed_rv, conflict_rv = self.insert_or_conflict(yaml_path, data, "code", engine_code)
        changed |= changed_rv
        conflict |= conflict_rv

        if Fuel:

            aliases = {
                "petrol": "petrol",
                "gasoline": "petrol",
                "essence": "petrol",

                "diesel": "diesel",
                "gazole": "diesel",
            }

            current = aliases.get(data.get("fuel", "").strip().lower(),
                                data.get("fuel", "").strip().lower())
            incoming = aliases.get(Fuel.strip().lower(),
                                Fuel.strip().lower())

            if not current:
                data["fuel"] = Fuel
                changed = True
            elif current != incoming:
                conflict = True
                changed |= self.add_conflict(
                    yaml_path,
                    data,
                    "fuel",
                    Fuel
                )

        evidences = data.setdefault("evidence", [])
        if not conflict:
            evidence = self.get_evidence_input()
            if evidence and evidence not in evidences:
                evidences.append(evidence)
                changed = True

        if changed:
            data["updated"] = current_timestamp()
            self.write_yaml(yaml_path, data)

            if new_file:
                self.log(f"Created Engine: {engine_ref}")
            else:
                self.log(f"Updated Engine: {engine_ref}")
        else:
            self.log(f"Engine unchanged: {engine_ref}")

        return engine_ref

    def on_import_worker(self, reader):
        for row in reader:
            Type = (row.get("Type") or "").strip()
            Brand = (row.get("Brand") or "").strip()
            Model = (row.get("Model") or "").strip()
            Year = (row.get("Year") or "").strip()
            Version = (row.get("Version") or "").strip()
            Engine = (row.get("Engine") or "").strip()
            Engine_type = (row.get("Engine_type") or "").strip()
            Fuel = (row.get("Fuel") or "").strip()
            Power_PS = (row.get("Power_PS") or "").strip()

            Power_KW = (
                0
                if Power_PS == ""
                else round(float(Power_PS) * 0.73549875)
            )

            Ecu_maker = (row.get("Ecu_maker") or "").strip()
            Ecu_model = (row.get("Ecu_model") or "").strip()
            ECU_type = (row.get("ECU_type") or "").strip()
            MCU = (row.get("MCU") or "").strip()

            ecu_relative_path = self.import_ecu(Ecu_maker, Ecu_model, ECU_type, MCU)
            engine_relative_path = self.import_engine(Brand, Engine, Engine_type, Fuel)
            self.import_vehicle(Type, Brand, Model, Year, Version, Power_KW, ecu_relative_path, engine_relative_path)
            self.heavy_op_step()

    def on_import(self):
        self.clear_log()

        if self.get_evidence_input() == "":
            messagebox.showerror(
                "Error",
                "Evidence source must be specified."
            )
            return

        text = self.input_text.get("1.0", "end-1c").strip()
        if text == "":
            self.log("Nothing to import.")
            return

        self.log("----------------------------------------")
        self.log("Starting vehicle import...")
        self.log("")

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        count = len(rows)
        self.heavy_op_start(
            self.on_import_worker,
            count,
            rows
        )

        self.log("")
        self.log("Import finished.")