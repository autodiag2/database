#!/usr/bin/python3
import os
import argparse
from datetime import datetime
import re
from vindecoder.decoder_data import *

class ISO3779_Decoder: 

    def __init__(self, vin: str, year: int = None):
        self.vin = vin
        self.year = year if year is not None else int(datetime.today().strftime('%Y'))
        self.wmi_raw = vin[:3]
        self.vds_raw = vin[3:9]
        self.vis_raw = vin[9:]
        self.decoder = self.vin_manufacturer_decoder()
        self.wmi = {
            "region":       self.ISO3780_wmi_region_str(), 
            "country":      self.ISO3780_wmi_country(), 
            "manufacturer": self.decode_manufacturer()
        }
        self.vds = self.decoder.vds_decode()
        self.vis = self.decoder.vis_decode()

    def ISO3780_wmi_region(self) -> ISO3780_WMI_REGION:
        for (start, end), region in ISO3780_WMI_REGIONS.items():
            if start <= self.vin[0] <= end:
                return region
        return ISO3780_WMI_REGION.unknown
    
    def ISO3780_wmi_region_str(self) -> str:
        return self.ISO3780_wmi_region().name

    def ISO3780_wmi_country(self) -> str:
        mapping = [chr(i) for i in range(ord('A'), ord('Z') + 1)] + [str(i) for i in range(1, 10)] + ['0']
        for (start, end), (country, code) in ISO3780_WMI_COUNTRIES.items():
            wmi_first = mapping.index(self.vin[0])
            wmi_first_start = mapping.index(start[0])
            wmi_first_end = mapping.index(end[0])
            if wmi_first_start <= wmi_first <= wmi_first_end:
                wmi_second = mapping.index(self.vin[1])
                wmi_second_start = mapping.index(start[1])
                wmi_second_end = mapping.index(end[1])
                if wmi_second_start <= wmi_second <= wmi_second_end:
                    return country
        return "unassigned"

    def wmi_manufacturer_is_less_500(self) -> bool:
        return self.vin[2] == '9'

    def decode_manufacturer(self) -> str:
        manufacturers_file = os.path.join(os.path.dirname(__file__), "data/manufacturers.tsv")
        if not os.path.exists(manufacturers_file):
            return "Unknown manufacturer"
        manufacturer_code = self.vin[11:14] if self.wmi_manufacturer_is_less_500() else None
        with open(manufacturers_file, "r") as file:
            for line in file:
                if line.startswith("#"): continue
                parts = line.strip().split("\t")
                if parts[0] == self.vin[:3]:
                    if manufacturer_code is None or (len(parts) > 2 and parts[2] == manufacturer_code):
                        return parts[1]
        return "Unknown manufacturer"
    
    def vin_manufacturer_decoder(self):
        manufacturer = self.decode_manufacturer()
        if any(x in manufacturer.lower() for x in ["citroen", "citroën"]):
            from vindecoder.decoder_modules.citroen import VIN_decoder_citroen
            return VIN_decoder_citroen(self)
        elif any(x in manufacturer.lower() for x in ["toyota"]):
            from vindecoder.decoder_modules.toyota import VIN_decoder_toyota
            return VIN_decoder_toyota(self)
        elif any(x in manufacturer.lower() for x in ["renault"]):
            from vindecoder.decoder_modules.renault import VIN_decoder_renault
            return VIN_decoder_renault(self)
        elif any(x in manufacturer.lower() for x in ["peugeot"]):
            from vindecoder.decoder_modules.peugeot import VIN_decoder_peugeot
            return VIN_decoder_peugeot(self)
        elif any(x in manufacturer.lower() for x in ["subaru"]):
            from vindecoder.decoder_modules.subaru import VIN_decoder_subaru
            return VIN_decoder_subaru(self)
        elif any(x in manufacturer.lower() for x in ["alfa romeo"]):
            from vindecoder.decoder_modules.alpha_romeo import VIN_decoder_alpha_romeo
            return VIN_decoder_alpha_romeo(self)
        else:
            from vindecoder.decoder_modules.none import VIN_decoder_none
            return VIN_decoder_none(self)

    def dump(self):
        region = self.ISO3780_wmi_region_str()
        vds_str = "\n                    ".join(f"{k}: {v}" for k, v in self.vds.items())
        vis_str = "\n                    ".join(f"{k}: {v}" for k, v in self.vis.items())
        
        print(f"""\
            dump {{
                wmi {{
                    region: {region}
                    country: {self.wmi['country']}
                    manufacturer: {self.wmi['manufacturer']}
                }}
                vds {{
                    {vds_str}
                }}
                vis {{
                    {vis_str}
                }}
            }}\
        """)

def is_valid_year(value):
    return re.fullmatch(r"\d{4}", value) is not None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("args", nargs="*", help="Arguments can include a year (YYYY) and VINs in any order")
    args = parser.parse_args()
    
    year = int(datetime.today().strftime('%Y'))
    vins = []
    
    for arg in args.args:
        if is_valid_year(arg):
            year = int(arg)
        else:
            vins.append(arg)
    
    if vins:
        for vin in vins:
            decoder = ISO3779_Decoder(vin, year)
            print(f"VIN: {vin}")
            decoder.dump()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()