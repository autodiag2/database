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

def slug(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9_.-]", "_", text)
    return text

def current_timestamp():
    return datetime.now(
        ZoneInfo("Europe/Paris")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")


# Type,Brand,Model,Year,Version,Engine,Engine_type,Fuel,Power_PS,Power,Ecu_maker,MCU_Type,MCU,Ecu_model,Connection_mode
# Car,Abarth,124 Spider,2008-2017,348,1400 MultiAir,55253268,Petrol,170,0,MARELLI,ECM,SPC564A80,8GMK,"BOOT, OBD"
class ImportVehicleTab(ImportTab):

    def __init__(self, parent, plain_path_var):
        super().__init__(parent, plain_path_var)

        self._build_configuration()
        self._build_input()
        self._build_buttons()
        self._build_output()

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

        MCU = MCU.strip()

        if MCU == "":
            return None

        manufacturer = self.guess_manufacturer_from_mcu_model(MCU)
        mcu_ref = f"{manufacturer}/{slug(MCU)}"

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

            with manufacturer_def.open(
                "w",
                encoding="utf-8"
            ) as fp:

                yaml.safe_dump(
                    {
                        "manufacturer": manufacturer
                    },
                    fp,
                    sort_keys=False,
                    allow_unicode=True
                )

        mcu_path = manufacturer_path / slug(MCU)
        mcu_path.mkdir(exist_ok=True)

        yaml_path = mcu_path / "def.yml"

        if yaml_path.exists():

            with yaml_path.open(
                "r",
                encoding="utf-8"
            ) as fp:

                data = yaml.safe_load(fp) or {}

            new_file = False

        else:

            data = {
                "created": current_timestamp(),
                "updated": current_timestamp(),
                "model": MCU,
                "evidence": []
            }

            new_file = True

        if data.get("model") != MCU:

            self.add_conflict(
                yaml_path,
                "model",
                data.get("model"),
                MCU
            )

            return mcu_ref

        changed = new_file

        evidence = data.setdefault("evidence", [])

        source = self.evidence_var.get().strip()

        if source and source not in evidence:
            evidence.append(source)
            changed = True

        if changed:

            data["updated"] = current_timestamp()

            with yaml_path.open(
                "w",
                encoding="utf-8"
            ) as fp:

                yaml.safe_dump(
                    data,
                    fp,
                    sort_keys=False,
                    allow_unicode=True
                )

            self.log(f"Updated MCU: {manufacturer}/{MCU}")
        else:
            self.log(f"MCU unchanged: {manufacturer}/{MCU}")

        return mcu_ref

    def import_ecu(self, Ecu_maker, Ecu_model, evidence, ECU_type, MCU = "ECM"):
        mcu_ref = self.import_mcu(MCU)
        # inspire from logic as mcu import but in ecu/Ecu_maker/def.yml
        #                                                      /EDC16C34/def.yml
        # with fields:
        #        model: 8GMK
        #        type: ECM
        #        mcu: mcu/stmicroelectronics/SPC564A80
        #        evidence: 
        #            - https://dev-srv.tlkeys.com/storage/files/pcmtuner/pcmtuner-detail-car-ecu-list.pdf
        # if mcu
        pass
    
    def on_import(self):
        self.clear_log()

        if self.evidence_var.get().strip() == "":
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
            ECU_type = (row.get("ECU_Type") or "").strip()
            MCU = (row.get("MCU") or "").strip()

            ecu_relative_path = self.import_ecu(Ecu_maker, Ecu_model, self.evidence_var.get(), ECU_type, MCU)
            # import engine
            # import vehicle
        
        # TODO
        self.log("[TODO] Create engines")
        self.log("[TODO] Create ECUs")
        self.log("[TODO] Create vehicles")
        self.log("[TODO] Create versions")
        self.log("[TODO] Merge YAML")
        self.log("[TODO] Detect conflicts")
        self.log("[TODO] Write files")

        self.log("")
        self.log("Import finished.")