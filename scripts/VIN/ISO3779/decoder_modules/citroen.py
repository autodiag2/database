import os

class ISO3779_decoder_citroen:
    def __init__(self, vin: str):
        self.vin = vin
        self.vds = {
            "family": self.family(), "outline": self.outline(),
            "engine_type": self.engine_type(), "engine_designation": self.engine_designation(),
            "gearbox": self.gear_box(), "depollution": self.depollution()
        }
    
    def _lookup_tsv(self, filename: str, column: int) -> str:
        file_path = os.path.join("data/VIN/manufacturer_specific_data/citroen", filename)
        if not os.path.exists(file_path):
            return "Unknown"
        
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("#"):
                    continue
                parts = line.strip().split("\t")
                if parts[0] == self.vin[4]:
                    return parts[column] if len(parts) > column else "Unknown"
        return "Unknown"
    
    def family(self) -> str:
        return self._lookup_tsv("family.tsv", 1)
    
    def outline(self) -> str:
        return self._lookup_tsv("outline.tsv", 1)
    
    def engine_type(self) -> str:
        return self._lookup_tsv("engine.tsv", 1)
    
    def engine_designation(self) -> str:
        return self._lookup_tsv("engine.tsv", 2)
    
    def gear_box(self) -> str:
        return self._lookup_tsv("version.tsv", 1)
    
    def depollution(self) -> str:
        return self._lookup_tsv("version.tsv", 2)
    
    def dump(self):
        print(f"VIN: {self.vin}")
        print("Decoded:")
        for key, value in self.vds.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    import sys
    vins = sys.argv[1:]
    for vin in vins:
        decoder = ISO3779_decoder_citroen(vin)
        decoder.dump()
