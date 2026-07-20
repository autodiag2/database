import sqlite3
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk

import manager.tk.tk as tk
from manager.tk.Tab import Tab


class StatsTab(Tab):
    def __init__(self, parent, sqlite_path_var: tk.StringVar):
        super().__init__(parent)

        self.sqlite_path_var = sqlite_path_var

        toolbar = tk.Frame(self.left_pane)
        toolbar.pack(fill="x", padx=5, pady=5)

        tk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh,
        ).pack(side="left")

        summary = tk.LabelFrame(self.left_pane, text="Summary")
        summary.pack(fill="x", padx=5, pady=5)

        self.summary_labels = {}

        fields = [
            "Manufacturers",
            "Vehicles",
            "Vehicle Versions",
            "Engines",
            "MCUs",
            "ECUs",
            "DTCs",
            "Knowledge Cutoff (raw)",
            "Peak Vehicle Versions",
        ]

        for i, field in enumerate(fields):
            tk.Label(summary, text=f"{field}:").grid(
                row=i,
                column=0,
                sticky="e",
                padx=4,
                pady=2,
            )

            lbl = tk.Label(summary, text="-")
            lbl.grid(
                row=i,
                column=1,
                sticky="w",
                padx=4,
                pady=2,
            )

            self.summary_labels[field] = lbl

        notebook = ttk.Notebook(self.left_pane)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        manufacturer_frame = tk.Frame(notebook)
        notebook.add(manufacturer_frame, text="Manufacturers")

        self.manufacturer_tree = ttk.Treeview(
            manufacturer_frame,
            columns=("manufacturer", "ecus", "engines"),
            show="headings",
        )

        self.manufacturer_tree.heading("manufacturer", text="Manufacturer")
        self.manufacturer_tree.heading("ecus", text="ECUs")
        self.manufacturer_tree.heading("engines", text="Engines")

        self.manufacturer_tree.column("manufacturer", width=220)
        self.manufacturer_tree.column("ecus", width=80, anchor="center")
        self.manufacturer_tree.column("engines", width=80, anchor="center")

        self.manufacturer_tree.pack(fill="both", expand=True)

        evidence_frame = tk.Frame(notebook)
        notebook.add(evidence_frame, text="Evidence")

        top = tk.Frame(evidence_frame)
        top.pack(fill="both", expand=True)

        bottom = tk.Frame(evidence_frame)
        bottom.pack(fill="both", expand=True)

        tk.Label(top, text="Unsourced Information").pack(anchor="w")

        self.unsourced_tree = ttk.Treeview(
            top,
            columns=("entity", "count"),
            show="headings",
            height=7,
        )

        self.unsourced_tree.heading("entity", text="Entity")
        self.unsourced_tree.heading("count", text="Count")

        self.unsourced_tree.column("entity", width=200)
        self.unsourced_tree.column("count", width=80, anchor="center")

        self.unsourced_tree.pack(fill="both", expand=True)

        tk.Label(bottom, text="Most Sourced").pack(anchor="w")

        self.sources_tree = ttk.Treeview(
            bottom,
            columns=("entity", "name", "sources"),
            show="headings",
            height=7,
        )

        self.sources_tree.heading("entity", text="Entity")
        self.sources_tree.heading("name", text="Name")
        self.sources_tree.heading("sources", text="Sources")

        self.sources_tree.column("entity", width=120)
        self.sources_tree.column("name", width=320)
        self.sources_tree.column("sources", width=80, anchor="center")

        self.sources_tree.pack(fill="both", expand=True)

        conflict_frame = tk.Frame(notebook)
        notebook.add(conflict_frame, text="Conflicts")

        self.conflict_tree = ttk.Treeview(
            conflict_frame,
            columns=("entity", "field", "count", "percent"),
            show="headings",
        )

        self.conflict_tree.heading("entity", text="Entity")
        self.conflict_tree.heading("field", text="Field")
        self.conflict_tree.heading("count", text="Count")
        self.conflict_tree.heading("percent", text="%")

        self.conflict_tree.pack(fill="both", expand=True)

        #self.refresh()

    def _connect(self):
        sqlite_file = Path(self.sqlite_path_var.get())

        if not sqlite_file.exists():
            messagebox.showerror(
                "Database Error",
                "SQLite database not found.",
            )
            return None

        conn = sqlite3.connect(sqlite_file)
        conn.row_factory = sqlite3.Row
        return conn

    def refresh(self):
        conn = self._connect()
        if conn is None:
            return

        cur = conn.cursor()

        self._load_summary(cur)
        self._load_manufacturers(cur)
        self._load_unsourced(cur)
        self._load_sources(cur)
        self._load_conflicts(cur)

        conn.close()

    def _load_summary(self, cur):
        cur.execute("""
            select
                (select count(*) from ad_manufacturer) as manufacturers,
                (select count(*) from ad_vehicle) as vehicles,
                (select count(*) from ad_vehicle_version) as vehicle_versions,
                (select count(*) from ad_engine) as engines,
                (select count(*) from ad_mcu) as mcus,
                (select count(*) from ad_ecu) as ecus,
                (select count(*) from ad_dtc) as dtcs;         
        """)
        counts = cur.fetchone()
        if not counts:
            print("nothing retrieved")
            return
        self.summary_labels["Manufacturers"].config(text=f"{counts[0]}")
        self.summary_labels["Vehicles"].config(text=f"{counts[1]}")
        self.summary_labels["Vehicle Versions"].config(text=f"{counts[2]}")
        self.summary_labels["Engines"].config(text=f"{counts[3]}")
        self.summary_labels["MCUs"].config(text=f"{counts[4]}")
        self.summary_labels["ECUs"].config(text=f"{counts[5]}")
        self.summary_labels["DTCs"].config(text=f"{counts[6]}")

        cur.execute("""
            with recursive

            parsed(version_id, start_year, end_year) as (
                select
                    id,
                    cast(substr(year, 1, 4) as integer),
                    case
                        when instr(year, '-') > 0 then
                            cast(substr(year, instr(year, '-') + 1, 4) as integer)
                        else
                            cast(substr(year, 1, 4) as integer)
                    end
                from ad_vehicle_version
                where year glob '[12][0-9][0-9][0-9]*'
            ),

            expanded(version_id, year, end_year) as (
                select version_id, start_year, end_year
                from parsed

                union all

                select
                    version_id,
                    year + 1,
                    end_year
                from expanded
                where year < end_year
            ),

            coverage as (
                select
                    year,
                    count(distinct version_id) as vehicle_versions
                from expanded
                group by year
            ),

            stats as (
                select max(vehicle_versions) as peak
                from coverage
            )

            select
                (select max(year) from coverage) as raw_cutoff,

                (
                    select max(c.year)
                    from coverage c
                    cross join stats s
                    where c.vehicle_versions >= s.peak * 0.10
                ) as estimated_cutoff,

                (
                    select max(vehicle_versions)
                    from coverage
                ) as peak_vehicle_versions;
        """)
        cutoff = cur.fetchone()
        if not cutoff:
            print("error")
            return
        self.summary_labels["Knowledge Cutoff (raw)"].config(text=f"{cutoff[0]}")
        self.summary_labels["Peak Vehicle Versions"].config(text=f"{cutoff[2]}")

    def _load_manufacturers(self, cur):
        self.manufacturer_tree.delete(
            *self.manufacturer_tree.get_children()
        )

        cur.execute("""
            select
                m.name as manufacturer,

                (
                    select count(*)
                    from ad_ecu e
                    where e.manufacturer_id = m.id
                ) as ecus,

                (
                    select count(*)
                    from ad_engine e
                    where e.manufacturer_id = m.id
                ) as engines

            from ad_manufacturer m
            order by
                m.name;
        """)
        rows = cur.fetchall()
        if not rows:
            print("error")
            return

        for row in rows:
            self.manufacturer_tree.insert(
                "",
                tk.END,
                values=(
                    row["manufacturer"],
                    row["ecus"],
                    row["engines"],
                ),
            )

    def _load_unsourced(self, cur):
        self.unsourced_tree.delete(
            *self.unsourced_tree.get_children()
        )

        cur.execute("""
            select 'Manufacturers' as entity, count(*) as count
            from ad_manufacturer m
            where not exists (
                select 1
                from ad_manufacturer_evidence me
                where me.manufacturer_id = m.id
            )

            union all

            select 'Vehicles', count(*)
            from ad_vehicle v
            where not exists (
                select 1
                from ad_vehicle_evidence ve
                where ve.vehicle_id = v.id
            )

            union all

            select 'Vehicle Versions', count(*)
            from ad_vehicle_version vv
            where not exists (
                select 1
                from ad_vehicle_version_evidence ve
                where ve.vehicle_version_id = vv.id
            )

            union all

            select 'Engines', count(*)
            from ad_engine e
            where not exists (
                select 1
                from ad_engine_evidence ee
                where ee.engine_id = e.id
            )

            union all

            select 'MCUs', count(*)
            from ad_mcu m
            where not exists (
                select 1
                from ad_mcu_evidence me
                where me.mcu_id = m.id
            )

            union all

            select 'ECUs', count(*)
            from ad_ecu e
            where not exists (
                select 1
                from ad_ecu_evidence ee
                where ee.ecu_id = e.id
            )

            union all

            select 'DTCs', count(*)
            from ad_dtc d
            where not exists (
                select 1
                from ad_dtc_evidence de
                where de.dtc_id = d.id
            )
        """)

        for row in cur.fetchall():
            self.unsourced_tree.insert(
                "",
                tk.END,
                values=(
                    row["entity"],
                    row["count"],
                ),
            )

    def _load_sources(self, cur):
        self.sources_tree.delete(
            *self.sources_tree.get_children()
        )

        cur.execute("""
            with all_sources as (

                select
                    'Manufacturer' as entity,
                    m.name as name,
                    count(me.evidence_id) as sources
                from ad_manufacturer m
                join ad_manufacturer_evidence me
                    on me.manufacturer_id = m.id
                group by m.id

                union all

                select
                    'Vehicle',
                    man.name || ' ' || v.model,
                    count(ve.evidence_id)
                from ad_vehicle v
                join ad_manufacturer man
                    on man.id = v.manufacturer_id
                join ad_vehicle_evidence ve
                    on ve.vehicle_id = v.id
                group by v.id

                union all

                select
                    'Vehicle Version',
                    man.name || ' ' || veh.model || ' ' || coalesce(v.version, '<generic>'),
                    count(vve.evidence_id)
                from ad_vehicle_version v
                join ad_vehicle veh
                    on veh.id = v.vehicle_id
                join ad_manufacturer man
                    on man.id = veh.manufacturer_id
                join ad_vehicle_version_evidence vve
                    on vve.vehicle_version_id = v.id
                group by v.id

                union all

                select
                    'Engine',
                    man.name || ' ' || e.code,
                    count(ee.evidence_id)
                from ad_engine e
                join ad_manufacturer man
                    on man.id = e.manufacturer_id
                join ad_engine_evidence ee
                    on ee.engine_id = e.id
                group by e.id

                union all

                select
                    'MCU',
                    man.name || ' ' || m.model,
                    count(me.evidence_id)
                from ad_mcu m
                join ad_manufacturer man
                    on man.id = m.manufacturer_id
                join ad_mcu_evidence me
                    on me.mcu_id = m.id
                group by m.id

                union all

                select
                    'ECU',
                    man.name || ' ' || e.model,
                    count(ee.evidence_id)
                from ad_ecu e
                join ad_manufacturer man
                    on man.id = e.manufacturer_id
                join ad_ecu_evidence ee
                    on ee.ecu_id = e.id
                group by e.id

                union all

                select
                    'DTC',
                    d.code || ' (' || man.name || '/' || ecu.model || ')',
                    count(de.evidence_id)
                from ad_dtc d
                join ad_ecu ecu
                    on ecu.id = d.ecu_id
                join ad_manufacturer man
                    on man.id = ecu.manufacturer_id
                join ad_dtc_evidence de
                    on de.dtc_id = d.id
                group by d.id
            )

            select
                entity,
                name,
                sources
            from all_sources
            order by
                sources desc,
                entity,
                name
        """)

        for row in cur.fetchall():
            self.sources_tree.insert(
                "",
                tk.END,
                values=(
                    row["entity"],
                    row["name"],
                    row["sources"],
                ),
            )

    def _load_conflicts(self, cur):
        self.conflict_tree.delete(
            *self.conflict_tree.get_children()
        )

        cur.execute("""
            with conflict_counts as (
                select
                    entity_type,
                    field,
                    count(*) as conflicts
                from ad_conflict
                group by
                    entity_type,
                    field
            ),
            total as (
                select
                    sum(conflicts) as total_conflicts
                from conflict_counts
            )

            select
                entity_type,
                field,
                conflicts,
                round(
                    100.0 * conflicts / total_conflicts,
                    2
                ) as percent
            from conflict_counts
            cross join total
            order by
                conflicts desc,
                entity_type,
                field;
        """)

        for row in cur.fetchall():
            self.conflict_tree.insert(
                "",
                tk.END,
                values=(
                    row["entity_type"],
                    row["field"],
                    row["conflicts"],
                    f"{row['percent']} %",
                ),
            )