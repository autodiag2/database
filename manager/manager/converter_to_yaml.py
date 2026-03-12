import sqlite3
import yaml
from pathlib import Path
import json
import shutil

class ConverterToYaml():

    def __init__(self, plain_text_db: Path = None, sqlite_db: Path = None):
        self.plain_text_db = Path(plain_text_db) if plain_text_db else None
        self.sqlite_db = Path(sqlite_db) if sqlite_db else None

    def _connect(self):
        conn = sqlite3.connect(self.sqlite_db)
        conn.execute("pragma foreign_keys = on")
        return conn

    def _from_json_text(self, value, default):
        if value is None or value == "":
            return default
        try:
            return json.loads(value)
        except:
            return default

    def _yaml_scalar_or_list(self, values):
        values = [v for v in values if v not in (None, "")]
        if len(values) == 0:
            return ""
        if len(values) == 1:
            return values[0]
        return values

    def _slug(self, value):
        value = (value or "").strip().lower()
        value = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in value)
        while "--" in value:
            value = value.replace("--", "-")
        value = value.strip("-")
        return value or "unknown"

    def _vehicle_scope_rows(self, cur, dtc_id):
        cur.execute("""
            select
                v.id as vehicle_id,
                vm.name as vehicle_manufacturer,
                v.model as vehicle_model,
                v.years as vehicle_years
            from ad_dtc_vehicle_link dvl
            join ad_vehicle v on v.id = dvl.vehicle_id
            left join ad_manufacturer vm on vm.id = v.manufacturer_id
            where dvl.dtc_id = ?
            order by vm.name, v.model, v.id
        """, (dtc_id,))
        vehicle_rows = cur.fetchall()

        scope_vehicles = []

        for vr in vehicle_rows:
            vehicle_id = vr["vehicle_id"]

            cur.execute("""
                select
                    m.name as manufacturer,
                    e.model as model,
                    e.type as type
                from ad_vehicle_ecu_link l
                join ad_ecu e on e.id = l.ecu_id
                left join ad_manufacturer m on m.id = e.manufacturer_id
                where l.vehicle_id = ?
                order by m.name, e.model, e.type
            """, (vehicle_id,))
            ecu_rows = cur.fetchall()

            cur.execute("""
                select
                    m.name as manufacturer,
                    e.model as model
                from ad_vehicle_engine_link l
                join ad_engine e on e.id = l.engine_id
                left join ad_manufacturer m on m.id = e.manufacturer_id
                where l.vehicle_id = ?
                order by m.name, e.model
            """, (vehicle_id,))
            engine_rows = cur.fetchall()

            if len(ecu_rows) == 0:
                ecu_rows = [{"manufacturer": "", "model": "", "type": ""}]

            if len(engine_rows) == 0:
                engine_rows = [{"manufacturer": "", "model": ""}]

            for er in engine_rows:
                for qr in ecu_rows:
                    scope_vehicles.append({
                        "manufacturer": vr["vehicle_manufacturer"] or "",
                        "model": vr["vehicle_model"] or "",
                        "engine": {
                            "manufacturer": er["manufacturer"] or "",
                            "model": er["model"] or ""
                        },
                        "ecu": {
                            "manufacturer": qr["manufacturer"] or "",
                            "model": qr["model"] or ""
                        },
                        "years": vr["vehicle_years"] if vr["vehicle_years"] not in (None, "") else "any"
                    })

        return scope_vehicles

    def _group_key_from_scope_vehicles(self, scope_vehicles):
        if len(scope_vehicles) == 0:
            return ("unknown", tuple(), tuple())

        manufacturers = sorted(set((v.get("manufacturer") or "").strip() for v in scope_vehicles))
        manufacturer_key = manufacturers[0] if len(manufacturers) > 0 and manufacturers[0] else "unknown"

        engine_keys = sorted(set(
            (
                ((v.get("engine") or {}).get("manufacturer") or "").strip(),
                ((v.get("engine") or {}).get("model") or "").strip()
            )
            for v in scope_vehicles
        ))

        ecu_keys = sorted(set(
            (
                ((v.get("ecu") or {}).get("manufacturer") or "").strip(),
                ((v.get("ecu") or {}).get("model") or "").strip()
            )
            for v in scope_vehicles
        ))

        return (manufacturer_key, tuple(engine_keys), tuple(ecu_keys))

    def to_yaml(self, progress_callback) -> bool:

        if self.plain_text_db is None or self.sqlite_db is None:
            return False

        root = self.plain_text_db / "vehicle"

        if root.exists():
            for p in root.iterdir():
                if p.is_dir():
                    shutil.rmtree(p)
        root.mkdir(parents=True, exist_ok=True)

        conn = self._connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            select
                d.id,
                d.code,
                d.definition,
                d.description,
                d.mil,
                d.created,
                d.updated,
                d.detection_condition,
                d.causes,
                d.repairs,
                d.evidence
            from ad_dtc d
            order by d.code
        """)

        rows = cur.fetchall()
        total = len(rows)
        count = 0
        progress_callback(count, total)

        grouped_payloads = {}

        for row in rows:
            dtc_id = row["id"]

            cur.execute("""
                select ds.name
                from ad_dtc_system_link l
                join ad_dtc_system ds on ds.id = l.system_id
                where l.dtc_id = ?
                order by ds.name
            """, (dtc_id,))
            systems = [r[0] for r in cur.fetchall()]

            cur.execute("""
                select ds.name
                from ad_dtc_subsystem_link l
                join ad_dtc_subsystem ds on ds.id = l.subsystem_id
                where l.dtc_id = ?
                order by ds.name
            """, (dtc_id,))
            subsystems = [r[0] for r in cur.fetchall()]

            cur.execute("""
                select dc.name
                from ad_dtc_category_link l
                join ad_dtc_category dc on dc.id = l.category_id
                where l.dtc_id = ?
                order by dc.name
            """, (dtc_id,))
            categories = [r[0] for r in cur.fetchall()]

            cur.execute("""
                select ds.name
                from ad_dtc_severity_link l
                join ad_dtc_severity ds on ds.id = l.severity_id
                where l.dtc_id = ?
                order by ds.name
            """, (dtc_id,))
            severities = [r[0] for r in cur.fetchall()]

            cur.execute("""
                select s.name
                from ad_dtc_standard_link l
                join ad_dtc_standard s on s.id = l.standard_id
                where l.dtc_id = ?
                order by s.name
            """, (dtc_id,))
            standards = [r[0] for r in cur.fetchall()]

            cur.execute("""
                select p.name
                from ad_dtc_protocol_link l
                join ad_diag_protocol p on p.id = l.protocol_id
                where l.dtc_id = ?
                order by p.name
            """, (dtc_id,))
            protocols = [r[0] for r in cur.fetchall()]

            cur.execute("""
                select d2.code
                from ad_dtc_related r
                join ad_dtc d2 on d2.id = r.related_dtc_id
                where r.dtc_id = ?
                order by d2.code
            """, (dtc_id,))
            related_codes = [r[0] for r in cur.fetchall()]

            scope_vehicles = self._vehicle_scope_rows(cur, dtc_id)

            payload = {
                "scope": {
                    "vehicle": scope_vehicles,
                    "protocol": protocols,
                    "standard": standards
                },
                "code": row["code"] or "",
                "system": self._yaml_scalar_or_list(systems),
                "subsystem": self._yaml_scalar_or_list(subsystems),
                "category": self._yaml_scalar_or_list(categories),
                "definition": row["definition"] or "",
                "description": row["description"] or "",
                "severity": self._yaml_scalar_or_list(severities),
                "mil": row["mil"] if row["mil"] is not None else "",
                "created": row["created"] or "",
                "updated": row["updated"] or "",
                "related_code": related_codes,
                "detection_condition": self._from_json_text(row["detection_condition"], []),
                "causes": self._from_json_text(row["causes"], []),
                "repairs": self._from_json_text(row["repairs"], []),
                "evidence": self._from_json_text(row["evidence"], {})
            }

            if not isinstance(payload["evidence"], dict):
                payload["evidence"] = {}

            group_key = self._group_key_from_scope_vehicles(scope_vehicles)
            grouped_payloads.setdefault(group_key, []).append(payload)

            count += 1
            progress_callback(count, total)

        conn.close()

        manufacturer_group_indices = {}

        sorted_group_items = sorted(
            grouped_payloads.items(),
            key=lambda item: (
                self._slug(item[0][0]),
                json.dumps(item[0][1], ensure_ascii=False),
                json.dumps(item[0][2], ensure_ascii=False),
            )
        )

        for group_key, payloads in sorted_group_items:
            manufacturer_name = group_key[0]
            manufacturer_slug = self._slug(manufacturer_name)

            manufacturer_group_indices[manufacturer_slug] = manufacturer_group_indices.get(manufacturer_slug, 0) + 1
            group_index = manufacturer_group_indices[manufacturer_slug]

            out_dir = root / manufacturer_slug / str(group_index) / "dtc"
            out_dir.mkdir(parents=True, exist_ok=True)

            payloads_sorted = sorted(payloads, key=lambda p: p.get("code", ""))

            for payload in payloads_sorted:
                code = payload.get("code", "") or "unknown"
                out_file = out_dir / f"{code}.yml"

                with open(out_file, "w", encoding="utf-8") as f:
                    yaml.safe_dump(
                        payload,
                        f,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False
                    )

        return True