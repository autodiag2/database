#!/usr/bin/python3
import os
import argparse
from datetime import datetime
import re
from decoder_data import *

class ISO3779_Decoder: 

    YEAR_MAPPING = {
        'M': "1991 or 2021", 'N': "1992 or 2022", 'P': "1993 or 2023", 'R': "1994 or 2024",
        'S': "1995 or 2025", 'T': "1996 or 2026", 'V': "1997 or 2027", 'W': "1998 or 2028",
        'X': "1999 or 2029", 'Y': "2000 or 2030", '1': "2001", '2': "2002", '3': "2003",
        '4': "2004", '5': "2005", '6': "2006", '7': "2007", '8': "2008", '9': "2009",
        'A': "2010", 'B': "2011", 'C': "2012", 'D': "2013", 'E': "2014", 'F': "2015",
        'G': "2016", 'H': "2017", 'J': "2018", 'K': "2019", 'L': "2020"
    }

    def __init__(self, year: int, vin: str):
        self.vin = vin
        self.year = year
        self.decoder = self.vin_manufacturer_decoder()
        self.vis = {"year": self.get_year(), "manufacturing_plant": self.decoder.vis_manufacturing_plant(), "serial_number": self.get_serial_number()}
        self.wmi = {"region": self.ISO3780_wmi_region_str(), "country": self.ISO3780_country(), "manufacturer": self.decode_manufacturer()}
        self.vds = self.decoder.vds_decode()

    def ISO3780_wmi_region(self) -> ISO3780_WMI_REGION:
        for (start, end), region in ISO3780_WMI_REGIONS.items():
            if start <= self.vin[:2] <= end:
                return region
        return ISO3780_WMI_REGION.unknown
    
    def ISO3780_wmi_region_str(self) -> str:
        return self.ISO3780_wmi_region().name

    def ISO3780_country(self) -> str:
        for (start, end), country in ISO3780_WMI_COUNTRIES.items():
            if start <= self.vin[:2] <= end:
                return country
        return "Unassigned"

    def manufacturer_is_less_500(self) -> bool:
        return self.vin[2] == '9'

    def decode_manufacturer(self) -> str:
        manufacturers_file = "data/VIN/manufacturers.tsv"
        if not os.path.exists(manufacturers_file):
            return "Unknown manufacturer"
        manufacturer_code = self.vin[11:14] if self.manufacturer_is_less_500() else None
        with open(manufacturers_file, "r") as file:
            for line in file:
                if line.startswith("#"): continue
                parts = line.strip().split("\t")
                if parts[0] == self.vin[:3]:
                    if manufacturer_code is None or (len(parts) > 2 and parts[2] == manufacturer_code):
                        return parts[1]
        return "Unknown manufacturer"
    
    def vin_manufacturer_decoder(self):
        region = self.ISO3780_wmi_region()
        manufacturer = self.decode_manufacturer()
        if any(x in manufacturer.lower() for x in ["citroen", "citroën"]):
            from decoder_modules.citroen import ISO3779_decoder_citroen
            return ISO3779_decoder_citroen(self.year, region, self.vin)
        elif any(x in manufacturer.lower() for x in ["toyota"]):
            from decoder_modules.toyota import ISO3779_decoder_toyota
            return ISO3779_decoder_toyota(self.year, region, self.vin)
        else:
            from decoder_modules.none import ISO3779_decoder_none
            return ISO3779_decoder_none(self.year, region, self.vin)

    def get_year(self) -> str:
        return self.YEAR_MAPPING.get(self.vin[9], "Unknown year")
    
    def get_manufacturing_plant(self) -> str:
        return self.vin[10]

    def get_serial_number(self) -> str:
        return self.vin[14:] if self.manufacturer_is_less_500() else self.vin[11:]

    def dump(self):
        region = self.ISO3780_wmi_region_str()
        vds_str = "\n                    ".join(f"{k}: {v}" for k, v in self.vds.items())
        
        print(f"""\
            dump {{
                wmi {{
                    region: {region}
                    country: {self.wmi['country']}
                    manufacturer: {self.wmi['manufacturer']}
                }}
                vis {{
                    year: {self.vis['year']}
                    serial number: {self.vis['serial_number']}
                    manufacturing_plant: {self.vis['manufacturing_plant']}
                }}
                vds {{
                    {vds_str}
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
    
    if not vins:
        vins = ["VF1BB05CF26010203", "VR7ACYHZKML019510", "VF7RD5FV8FL507366", "JTMBF4DV4A5037027"]
    for vin in vins:
        decoder = ISO3779_Decoder(year, vin)
        print(f"VIN: {vin}")
        decoder.dump()

if __name__ == "__main__":
    main()