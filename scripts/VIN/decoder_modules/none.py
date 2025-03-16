from decoder_modules.module import VIN_decoder_module
from decoder import ISO3779_Decoder

class VIN_decoder_none(VIN_decoder_module):

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "")
    
    def vds_decode(self):
        return {}