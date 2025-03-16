# https://citroen.c5x7.fr/vin
import os
from decoder_modules.module import VIN_decoder_module
from decoder import ISO3779_Decoder

class VIN_decoder_citroen(VIN_decoder_module):

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "data/VIN/manufacturer_specific_data/citroen")
    
    def vds_decode(self):
        return {
            "family": self.family(), "outline": self.outline(),
            "engine_type": self.engine_type(), "engine_designation": self.engine_designation(),
            "gearbox": self.gear_box(), "depollution": self.depollution()
        }

    def family(self) -> str:
        return self.lookup_tsv("family.tsv", self.rootDecoder.vds_raw[0:1], 1)
    
    def outline(self) -> str:
        return self.lookup_tsv("outline.tsv", self.rootDecoder.vds_raw[1:2], 1)
    
    def engine_type(self) -> str:
        return self.lookup_tsv("engine.tsv", self.rootDecoder.vds_raw[2:5], 1)
    
    def engine_designation(self) -> str:
        return self.lookup_tsv("engine.tsv", self.rootDecoder.vds_raw[2:5], 2)
    
    def gear_box(self) -> str:
        return self.lookup_tsv("version.tsv", self.rootDecoder.vds_raw[5:6], 1)
    
    def depollution(self) -> str:
        return self.lookup_tsv("version.tsv", self.rootDecoder.vds_raw[5:6], 2)


