from decoder_modules.module import ISO3779_decoder_module
from decoder import ISO3779_Decoder

class ISO3779_decoder_none(ISO3779_decoder_module):

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "")
    
    def vds_decode(self):
        return {}