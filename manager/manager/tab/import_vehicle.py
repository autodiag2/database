import manager.tk.tk as tk
from manager.tab.import_tab import ImportTab
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv


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

    def on_import(self):
        self.clear_log()

        if self.evidence_var.get().strip() == "":
            messagebox.showerror(
                "Error",
                "Evidence source must be specified."
            )
            return

        if self.input_text.get("1.0", "end-1c").strip() == "":
            self.log("Nothing to import.")
            return

        self.log("----------------------------------------")
        self.log("Starting vehicle import...")
        self.log("")

        # TODO
        self.log("[TODO] Parse CSV")
        self.log("[TODO] Create manufacturers")
        self.log("[TODO] Create engines")
        self.log("[TODO] Create ECUs")
        self.log("[TODO] Create vehicles")
        self.log("[TODO] Create versions")
        self.log("[TODO] Merge YAML")
        self.log("[TODO] Detect conflicts")
        self.log("[TODO] Write files")

        self.log("")
        self.log("Import finished.")