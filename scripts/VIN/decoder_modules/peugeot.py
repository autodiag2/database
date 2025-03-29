import os
from decoder_modules.module import VIN_decoder_module
from decoder import ISO3779_Decoder

class VIN_decoder_peugeot(VIN_decoder_module):

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "data/VIN/manufacturer_specific_data/peugeot")
    
    def vis_get_manufacturing_plant(self) -> str:
        return self.lookup_tsv("plant.tsv", self.rootDecoder.vis_raw[1], 1)
    
    def vds_decode(self):
        return {
            
        }