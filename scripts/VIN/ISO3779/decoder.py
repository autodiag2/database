#!/usr/bin/python3
import os, sys
from typing import Optional

class ISO3779_Decoder:
    ISO3779_WMI_COUNTRIES = {
        ("AA", "AH"): "South Africa", ("AJ", "AN"): "Ivory Coast", ("AP", "A0"): "Unassigned",
        ("BA", "BE"): "Angola", ("BF", "BK"): "Kenya", ("BL", "BR"): "Tanzania",
        ("BS", "B0"): "Unassigned", ("CA", "CE"): "Benin", ("CF", "CK"): "Madagascar",
        ("CL", "CR"): "Tunisia", ("CS", "C0"): "Unassigned", ("DA", "DE"): "Egypt",
        ("DF", "DK"): "Morocco", ("DL", "DR"): "Zambia", ("DS", "D0"): "Unassigned",
        ("EA", "EE"): "Ethiopia", ("EF", "EK"): "Mozambique", ("EL", "E0"): "Unassigned",
        ("FA", "FE"): "Ghana", ("FF", "FK"): "Nigeria", ("FL", "F0"): "Unassigned",
        ("GA", "G0"): "Unassigned", ("HA", "H0"): "Unassigned", ("JA", "J0"): "Japan",
        ("KA", "KE"): "Sri Lanka", ("KF", "KK"): "Israel", ("KL", "KR"): "South Korea",
        ("KS", "K0"): "Unassigned", ("LA", "L0"): "China", ("MA", "ME"): "India",
        ("MF", "MK"): "Indonesia", ("ML", "MR"): "Thailand", ("MS", "M0"): "Unassigned",
        ("NF", "NK"): "Pakistan", ("NL", "NR"): "Turkey", ("NS", "N0"): "Unassigned",
        ("PA", "PE"): "Philippines", ("PF", "PK"): "Singapore", ("PL", "PR"): "Malaysia",
        ("PS", "P0"): "Unassigned", ("RA", "RE"): "United Arab Emirates", ("RF", "RK"): "Taiwan",
        ("RL", "RR"): "Vietnam", ("RS", "R0"): "Unassigned", ("SA", "SM"): "Great Britain",
        ("VF", "VR"): "France", ("WA", "W0"): "Germany", ("ZA", "ZR"): "Italy",
    }

    YEAR_MAPPING = {
        'M': "1991 or 2021", 'N': "1992 or 2022", 'P': "1993 or 2023", 'R': "1994 or 2024",
        'S': "1995 or 2025", 'T': "1996 or 2026", 'V': "1997 or 2027", 'W': "1998 or 2028",
        'X': "1999 or 2029", 'Y': "2000 or 2030", '1': "2001", '2': "2002", '3': "2003",
        '4': "2004", '5': "2005", '6': "2006", '7': "2007", '8': "2008", '9': "2009",
        'A': "2010", 'B': "2011", 'C': "2012", 'D': "2013", 'E': "2014", 'F': "2015",
        'G': "2016", 'H': "2017", 'J': "2018", 'K': "2019", 'L': "2020"
    }

    def __init__(self, vin: str):
        self.vin = vin
        self.wmi = {"country": self.decode_country(), "manufacturer": self.decode_manufacturer()}
        self.vis = {"year": self.get_year(), "serial_number": self.get_serial_number()}
        self.vds = self.vds_decoder()

    def decode_region(self) -> str:
        if "A" <= self.vin[0] <= "H": return "Africa"
        if "J" <= self.vin[0] <= "R": return "Asia"
        if "S" <= self.vin[0] <= "Z": return "Europe"
        if "1" <= self.vin[0] <= "5": return "North America"
        if "6" <= self.vin[0] <= "7": return "Oceania"
        if "8" <= self.vin[0] <= "9": return "South America"
        return "Unknown"

    def decode_country(self) -> str:
        for (start, end), country in self.ISO3779_WMI_COUNTRIES.items():
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
    
    def vds_decoder(self):
        from decoder_modules.citroen import ISO3779_decoder_citroen
        return ISO3779_decoder_citroen(self.vin)

    def get_year(self) -> str:
        return self.YEAR_MAPPING.get(self.vin[9], "Unknown year")

    def get_serial_number(self) -> str:
        return self.vin[14:] if self.manufacturer_is_less_500() else self.vin[11:]

    def dump(self):
        region = self.decode_region()
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
    }}
{self.vds.dump_string("    ")}
}}\
""")

if __name__ == "__main__":
    vins = sys.argv[1:]
    if not vins:
        vins = ["VF1BB05CF26010203", "VR7ACYHZKML019510"]  # Default VIN for testing
    
    for vin in vins:
        decoder = ISO3779_Decoder(vin)
        print(f"VIN:{vin}")
        decoder.dump()