import os
from decoder_modules.module import VIN_decoder_module
from decoder import ISO3779_Decoder

class VIN_decoder_renault(VIN_decoder_module):

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "data/VIN/manufacturer_specific_data/renault")
    
    def vds_decode(self):
        return {
            "body": self.p3rd_body(), "project_code": self.p3rd_project_code(),
            "engine_hint": self.p3rd_engine_hint(), "plant": self.vds_get_plant()
        }
    
    def vis_decode(self):
        return {
            "year": self.vis_get_year(), 
            "serial_number": self.rootDecoder.vis_raw[1:]
        }
    
    def vds_get_plant(self):
        return self.lookup_tsv("plant.tsv", self.rootDecoder.vds_raw[5], 1)

    def p3rd_body(self):
        return self.lookup_tsv("body.tsv", self.rootDecoder.vds_raw[0], 1)

    def p3rd_project_code(self):
        return self.lookup_tsv("3rd_period/project_code.tsv", self.rootDecoder.vds_raw[1], 1)
    
    def p3rd_engine_hint(self):
        return self.lookup_tsv("3rd_period/engine_hint.tsv", self.rootDecoder.vds_raw[2:4], 1)