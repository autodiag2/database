import manager.dtc as dtc
import manager.tk.tk as tk
from manager.tab.import_tab import ImportTab
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml

def current_timestamp():
    return datetime.now(
        ZoneInfo("Europe/Paris")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")

def parse_lines(text):
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split(None, 1)

        if len(parts) != 2:
            yield None, None, line
            continue

        yield parts[0].upper(), parts[1].strip(), None

class ImportCodesTab(ImportTab):

    def add_conflict(self, filename, code, existing_definition, imported_definition, obj):
        frame = tk.LabelFrame(self.conflict_container, text=code)
        frame.pack(fill="x", padx=5, pady=5)

        tk.Label(frame, text="Current").grid(row=0, column=0, sticky="nw", padx=5, pady=2)

        current = tk.Text(frame, height=4, width=45)
        current.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        current.insert("1.0", existing_definition)
        current.configure(state="disabled")

        tk.Label(frame, text="Imported").grid(row=0, column=1, sticky="nw", padx=5, pady=2)

        incoming = tk.Text(frame, height=4, width=45)
        incoming.grid(row=1, column=1, sticky="nsew", padx=5, pady=2)
        incoming.insert("1.0", imported_definition)
        incoming.configure(state="disabled")

        conflict = {
            "filename": filename,
            "code": code,
            "obj": obj
        }

        tk.Button(
            frame,
            text="Still right",
            command=lambda c=conflict, f=frame: self.accept_conflict(c, f)
        ).grid(row=2, column=0, sticky="w", padx=5, pady=5)

        tk.Button(
            frame,
            text="Discard",
            command=frame.destroy
        ).grid(row=2, column=1, sticky="e", padx=5, pady=5)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def __init__(self, parent, plain_path_var):
        super().__init__(parent, plain_path_var)

        self.conflict_container = self.right_pane
        self._build_configuration()
        self._build_input()
        self._build_buttons()
        self._add_log_widget()

    def _build_configuration(self):
        frame = tk.LabelFrame(self.left_pane, text="Destination")
        frame.pack(fill="x", padx=10, pady=10)

        tk.Label(frame, text="Manufacturer:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.manufacturer_var = tk.StringVar()
        self.manufacturer_var.set("bosch")
        tk.Entry(frame, textvariable=self.manufacturer_var, width=40).grid(
            row=0, column=1, sticky="we", padx=5, pady=3
        )

        tk.Label(frame, text="ECU model:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.ecu_var = tk.StringVar()
        self.ecu_var.set("EDC16C34")
        tk.Entry(frame, textvariable=self.ecu_var, width=40).grid(
            row=1, column=1, sticky="we", padx=5, pady=3
        )

        tk.Label(frame, text="Evidence source:").grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.evidence_var = tk.StringVar(value="http://example.com")
        tk.Entry(frame, textvariable=self.evidence_var, width=40).grid(
            row=2, column=1, sticky="we", padx=5, pady=3
        )

        frame.columnconfigure(1, weight=1)

    def _build_input(self):
        frame = tk.LabelFrame(self.left_pane , text="Codes to import")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.input_text = tk.Text(
            frame,
            wrap="none",
            height=18
        )
        self.input_text.insert(
            "1.0",
            """P1111  some definition
        """
        )

        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.input_text.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.input_text.xview)

        self.input_text.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.input_text.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_buttons(self):
        frame = tk.Frame(self.left_pane )
        frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(
            frame,
            text="Copy",
            command=self.on_copy
        ).pack(side="left")

        tk.Button(
            frame,
            text="Paste",
            command=self.on_paste
        ).pack(side="left", padx=5)

        tk.Button(
            frame,
            text="Clear",
            command=self.on_clear
        ).pack(side="left", padx=5)

        ttk.Separator(frame, orient="vertical").pack(
            side="left",
            fill="y",
            padx=10
        )

        tk.Button(
            frame,
            text="Import",
            command=self.on_import
        ).pack(side="left")

    def accept_conflict(self, conflict, frame):

        obj = conflict["obj"]

        evidence = obj.setdefault("evidence", {})
        sources = evidence.setdefault("source", [])

        if self.get_evidence_input() not in sources:
            sources.append(self.get_evidence_input())

        obj["updated"] = current_timestamp()

        with open(conflict["filename"], "w", encoding="utf-8") as fp:
            yaml.safe_dump(
                obj,
                fp,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )

        self.log(f"[OK] {conflict['code']}: evidence added after manual confirmation.")

        frame.destroy()

    def on_copy(self):
        text = self.input_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def on_paste(self):
        try:
            text = self.root.clipboard_get()
        except Exception:
            return

        self.input_text.insert("insert", text)

    def on_clear(self):
        self.input_text.delete("1.0", "end")

    def get_destination_folder(self):
        manufacturer = self.manufacturer_var.get().strip().lower()
        ecu = self.ecu_var.get().strip().lower()

        if manufacturer == "":
            raise ValueError("Manufacturer must be specified.")

        if ecu:
            return self.get_data_src() / "ecu" / manufacturer / ecu

        return self.get_data_src() / "ecu" / "generic" / manufacturer

    def on_import(self):
        self.clear_log()
        self.conflicts = []
        if not self.get_data_src().exists():
            messagebox.showerror(
                "Error",
                "data-src directory does not exist."
            )
            return

        try:
            destination = self.get_destination_folder()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.log(f"Destination : {destination}")

        text = self.input_text.get("1.0", "end-1c")

        if text.strip() == "":
            self.log("Nothing to import.")
            return

        self.log("----------------------------------------")
        self.log("Starting import...")
        self.log("")

        self.import_text(text, destination)

        self.log("Imported !")

    def import_text(self, text: str, destination: Path):
        destination.mkdir(parents=True, exist_ok=True)

        codes_dir = destination / "codes"
        codes_dir.mkdir(parents=True, exist_ok=True)

        self.log(f"Created folder: {codes_dir}")

        imported = 0
        warnings = 0
        errors = 0

        for code, definition, error_return in parse_lines(text):

            if code == definition == None: 
                self.log(f"[ERROR] line not understood: {error_return}")
                continue

            if not dtc.is_saej2012_2002(code):
                self.log(f"[ERROR] {code}: unsupported code format")
                errors += 1
                continue

            if not dtc.is_manufacturer_specific_saej2012_2002(code):
                self.log(f"[WARNING] {code}: generic SAEJ2012 code ignored")
                warnings += 1
                continue

            filename = codes_dir / f"{code}.yml"

            if filename.exists():
                self.log(f"[WARNING] {filename.name} already exists, overwritten")

            if self.write_yaml(filename, code, definition):
                self.log(f"[OK] {filename}")
                imported += 1
            else:
                errors += 1

        self.log("")
        self.log(f"Imported : {imported}")
        self.log(f"Warnings: {warnings}")
        self.log(f"Errors  : {errors}")

    def yaml_object(self, code, definition):

        now = current_timestamp()

        protocol = []
        standard = []

        if dtc.is_saej2012_2002(code):
            protocol.append("obd2")
            standard.append("saej2012.2002")

        return {
            "code": code,
            "system": "",
            "subsystem": "",
            "category": "",
            "definition": definition,
            "description": "",
            "severity": "",
            "mil": "",
            "created": now,
            "updated": now,
            "related_code": [],
            "detection_condition": [],
            "causes": [],
            "repairs": [],
            "evidence": {
                "source": [
                    self.get_evidence_input()
                ]
            },
            "protocol": protocol,
            "standard": standard
        }

    def get_evidence_input(self):
        return self.evidence_var.get().strip()

    def write_yaml(self, filename: Path, code: str, definition: str):

        if filename.exists():

            with open(filename, "r", encoding="utf-8") as fp:
                obj = yaml.safe_load(fp)

            existing_definition = (
                str(obj.get("definition", ""))
                .strip()
                .replace("“", '"')
                .replace("”", '"')
            )

            imported_definition = (
                definition
                .strip()
                .replace("“", '"')
                .replace("”", '"')
            )

            if existing_definition != imported_definition:
                self.log(
                    f"[WARNING] {code}: definition mismatch, file not modified."
                )
                self.log(f"          Existing: {existing_definition}")
                self.log(f"          Imported: {imported_definition}")
                self.add_conflict(
                    filename,
                    code,
                    existing_definition,
                    imported_definition,
                    obj
                )
                return False

            evidence = obj.setdefault("evidence", {})
            sources = evidence.setdefault("source", [])

            if self.get_evidence_input() == "":
                self.log("[WARNING] no evidence provided")
            else:
                if self.get_evidence_input() not in sources:
                    sources.append(self.get_evidence_input())
                    self.log(
                        f"[OK] {code}: added evidence source '{self.get_evidence_input()}'."
                    )
                else:
                    self.log(
                        f"[OK] {code}: evidence source already present."
                    )

            obj["updated"] = current_timestamp()
            with open(filename, "w", encoding="utf-8") as fp:
                yaml.safe_dump(
                    obj,
                    fp,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False
                )

            return True

        obj = self.yaml_object(code, definition)

        with open(filename, "w", encoding="utf-8") as fp:
            yaml.safe_dump(
                obj,
                fp,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )

        self.log(f"[OK] Created {filename.name}")

        return True