import os
from decoder_modules.module import ISO3779_decoder_module

class ISO3779_decoder_citroen(ISO3779_decoder_module):
    def __init__(self, vin: str):
        super().__init__(vin, "data/VIN/manufacturer_specific_data/citroen")
        self.vds = {
            "family": self.family(), "outline": self.outline(),
            "engine_type": self.engine_type(), "engine_designation": self.engine_designation(),
            "gearbox": self.gear_box(), "depollution": self.depollution()
        }
    
    def family(self) -> str:
        return self._lookup_tsv("family.tsv", 1, self.vds_raw[0:1])
    
    def outline(self) -> str:
        return self._lookup_tsv("outline.tsv", 1, self.vds_raw[1:2])
    
    def engine_type(self) -> str:
        return self._lookup_tsv("engine.tsv", 1, self.vds_raw[2:5])
    
    def engine_designation(self) -> str:
        return self._lookup_tsv("engine.tsv", 2, self.vds_raw[2:5])
    
    def gear_box(self) -> str:
        return self._lookup_tsv("version.tsv", 1, self.vds_raw[5:6])
    
    def depollution(self) -> str:
        return self._lookup_tsv("version.tsv", 2, self.vds_raw[5:6])
    
    def dump_string(self, padding):
        result = f"{padding}vds:{{\n"
        for key, value in self.vds.items():
            result += f"{padding}   {key}:\t{value}\n"
        result += f"{padding}}}\n"
        return result

