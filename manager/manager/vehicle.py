from pathlib import Path
import configparser

class Vehicle:
    def __init__(self, path: Path):
        self.path = path
        self.desc_path = path / "desc.ini"
        self.codes_path = path / "codes.tsv"
        self.data = {}  # keys: manufacturer, engine, ecu, years
        self.dtcs = []  # list of (code, description)
        self.load()

    def duplicated_count(self) -> int:
        seen = set()
        dup = set()
        for code, _ in self.dtcs:
            if code in seen:
                dup.add(code)
            else:
                seen.add(code)
        return len(dup)

    def malformed_count(self) -> int:
        c = 0
        for code, desc in self.dtcs:
            if not code or not desc:
                c += 1
        return c

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