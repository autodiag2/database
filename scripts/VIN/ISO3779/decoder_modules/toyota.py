
import os, sys
from decoder_modules.module import ISO3779_decoder_module

class ISO3779_decoder_toyota(ISO3779_decoder_module):

    def __init__(self, vin: str):
        super().__init__(vin, "data/VIN/manufacturer_specific_data/toyota")
        self.wmi = {
            "vehicle_type": self.vehicle_type()
        }

    def vehicle_type(self):
        return self.lookup_tsv("vehicle_type.tsv", 1, self.vin[2])

    def dump_string(self, padding):
        result = f"{padding}wmi:{{\n"
        for key, value in self.wmi.items():
            result += f"{padding}   {key}:\t{value}\n"
        result += f"{padding}}}\n"
        return result