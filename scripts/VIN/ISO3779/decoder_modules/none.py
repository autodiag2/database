from decoder_modules.module import ISO3779_decoder_module

class ISO3779_decoder_none(ISO3779_decoder_module):

    def __init__(self, year: int, region: str, vin: str):
        super().__init__(vin, "", year)
    
    def vds_decode(self):
        return {}