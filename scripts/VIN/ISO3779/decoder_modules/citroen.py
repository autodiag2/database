import os
from decoder_modules.module import ISO3779_decoder_module

class ISO3779_decoder_citroen(ISO3779_decoder_module):
    def __init__(self, vin: str, year: int):
        super().__init__(vin, "data/VIN/manufacturer_specific_data/citroen", year)
        self.vds = {
            "family": self.family(), "outline": self.outline(),
            "engine_type": self.engine_type(), "engine_designation": self.engine_designation(),
            "gearbox": self.gear_box(), "depollution": self.depollution()
        }
    
    def family(self) -> str:
        return self.lookup_tsv("family.tsv", self.vds_raw[0:1], 1)
    
    def outline(self) -> str:
        return self.lookup_tsv("outline.tsv", self.vds_raw[1:2], 1)
    
    def engine_type(self) -> str:
        return self.lookup_tsv("engine.tsv", self.vds_raw[2:5], 1)
    
    def engine_designation(self) -> str:
        return self.lookup_tsv("engine.tsv", self.vds_raw[2:5], 2)
    
    def gear_box(self) -> str:
        return self.lookup_tsv("version.tsv", self.vds_raw[5:6], 1)
    
    def depollution(self) -> str:
        return self.lookup_tsv("version.tsv", self.vds_raw[5:6], 2)
    
    def dump_string(self, padding):
        result = f"{padding}vds:{{\n"
        for key, value in self.vds.items():
            result += f"{padding}   {key}:\t{value}\n"
        result += f"{padding}}}\n"
        return result

