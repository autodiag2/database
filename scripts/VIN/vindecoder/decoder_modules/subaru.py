import os
from vindecoder.decoder_modules.module import VIN_decoder_module
from vindecoder.decoder import ISO3779_Decoder

class VIN_decoder_subaru(VIN_decoder_module):

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "data/manufacturer_specific/subaru")
    
    def vis_get_manufacturing_plant(self) -> str:
        return self.lookup_tsv("plant_transmission.tsv", self.rootDecoder.vis_raw[1], 1)
    
    def vis_get_transmission(self) -> str:
        return self.lookup_tsv("plant_transmission.tsv", self.rootDecoder.vis_raw[1], 2)
    
    def vds_decode(self):
        return {
            "line_type": self.vds_line_type(),
            "body_style": self.vds_body_style(),
            "engine_type": self.vds_engine_type(),
            "model": self.vds_model(),
            "retraint_type or weight_class": self.vds_rst_or_wc()
        }
    
    def vds_line_type(self):
        return self.lookup_tsv("line_type.tsv", self.rootDecoder.vds_raw[0], 1)
    
    def vds_body_style(self):
        return self.lookup_tsv("body_style.tsv", self.rootDecoder.vds_raw[1], 1)
    
    def vds_engine_type(self):
        return self.lookup_tsv("engine_type.tsv", self.rootDecoder.vds_raw[2], 1)
    
    def vds_model(self):
        return self.lookup_tsv("model.tsv", self.rootDecoder.vds_raw[3], 1)
    
    def vds_rst_or_wc(self):
        return self.lookup_tsv("restraint_type.tsv", self.rootDecoder.vds_raw[4], 1)

    def vis_decode(self):
        vis_decoded = super().vis_decode()
        vis_decoded["transmission"] = self.vis_get_transmission()
        return vis_decoded