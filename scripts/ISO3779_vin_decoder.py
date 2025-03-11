import os
from typing import Optional

class ISO3779_Decoded:
    def __init__(self):
        self.wmi = {
            "country": None,
            "manufacturer": None
        }
        self.vis = {
            "year": None,
            "serial_number": None
        }

def ISO3779_decode_region_from(vin: str) -> str:
    if "A" <= vin[0] <= "H":
        return "Africa"
    if "J" <= vin[0] <= "R":
        return "Asia"
    if "S" <= vin[0] <= "Z":
        return "Europe"
    if "1" <= vin[0] <= "5":
        return "North America"
    if "6" <= vin[0] <= "7":
        return "Oceania"
    if "8" <= vin[0] <= "9":
        return "South America"
    return "Unknown"

ISO3779_WMI_COUNTRIES = {
    ("AA", "AH"): "South Africa",
    ("AJ", "AN"): "Ivory Coast",
    ("JA", "J0"): "Japan",
    ("KA", "KE"): "Sri Lanka",
    ("KL", "KR"): "South Korea",
    ("LA", "L0"): "China",
    ("MA", "ME"): "India",
    ("NF", "NK"): "Pakistan",
    ("SA", "SM"): "Great Britain",
    ("VF", "VR"): "France",
    ("WA", "W0"): "Germany",
    ("ZA", "ZR"): "Italy",
    ("BA", "BE"): "Angola",
    ("BF", "BK"): "Kenya",
    ("BL", "BR"): "Tanzania",
    ("CF", "CK"): "Madagascar",
    ("CL", "CR"): "Tunisia",
    ("DA", "DE"): "Egypt",
    ("DF", "DK"): "Morocco",
    ("DL", "DR"): "Zambia",
    ("FA", "FE"): "Ghana",
    ("FF", "FK"): "Nigeria",
    ("KF", "KK"): "Israel",
    ("MF", "MK"): "Indonesia",
    ("ML", "MR"): "Thailand",
    ("NL", "NR"): "Turkey",
    ("PA", "PE"): "Philippines",
    ("PF", "PK"): "Singapore",
    ("PL", "PR"): "Malaysia",
    ("RF", "RK"): "Taiwan",
    ("RL", "RR"): "Vietnam",
    ("SN", "ST"): "Germany",
    ("SU", "SZ"): "Poland",
    ("TA", "TH"): "Switzerland",
    ("TJ", "TP"): "Czech Republic",
    ("TR", "TV"): "Hungary",
    ("VF", "VR"): "France",
    ("VS", "VW"): "Spain",
    ("WA", "W0"): "Germany",
    ("XA", "XE"): "Bulgaria",
    ("XF", "XK"): "Greece",
    ("XL", "XR"): "Netherlands",
    ("XS", "XW"): "Russia",
    ("ZA", "ZR"): "Italy"
}

def ISO3779_decode_country_from(vin: str) -> str:
    for (start, end), country in ISO3779_WMI_COUNTRIES.items():
        if start <= vin[:2] <= end:
            return country
    return "Unassigned"

def ISO3779_wmi_manufacturer_is_less_500(vin: str) -> bool:
    return vin[2] == '9'

def ISO3779_decode_manufacturer_from(vin: str) -> str:
    manufacturers_file = "data/VIN/manufacturers.tsv"
    if not os.path.exists(manufacturers_file):
        return "Unknown manufacturer"
    
    manufacturer_code = vin[11:14] if ISO3779_wmi_manufacturer_is_less_500(vin) else None
    with open(manufacturers_file, "r") as file:
        for line in file:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if parts[0] == vin[:3]:
                if manufacturer_code is None or (len(parts) > 2 and parts[2] == manufacturer_code):
                    return parts[1]
    return "Unknown manufacturer"

def ISO3779_vis_get_year_from(vin: str) -> str:
    year_mapping = {
        'M': "1991 or 2021", 'N': "1992 or 2022", 'P': "1993 or 2023", 'R': "1994 or 2024",
        'S': "1995 or 2025", 'T': "1996 or 2026", 'V': "1997 or 2027", 'W': "1998 or 2028",
        'X': "1999 or 2029", 'Y': "2000 or 2030", '1': "2001", '2': "2002", '3': "2003",
        '4': "2004", '5': "2005", '6': "2006", '7': "2007", '8': "2008", '9': "2009",
        'A': "2010", 'B': "2011", 'C': "2012", 'D': "2013", 'E': "2014", 'F': "2015",
        'G': "2016", 'H': "2017", 'J': "2018", 'K': "2019", 'L': "2020"
    }
    return year_mapping.get(vin[9], "Unknown year")

def ISO3779_vis_serial_number_from(vin: str) -> str:
    return vin[14:] if ISO3779_wmi_manufacturer_is_less_500(vin) else vin[11:]

def ISO3779_decode_from(vin: str) -> ISO3779_Decoded:
    vin_decoded = ISO3779_Decoded()
    vin_decoded.wmi["country"] = ISO3779_decode_country_from(vin)
    vin_decoded.wmi["manufacturer"] = ISO3779_decode_manufacturer_from(vin)
    vin_decoded.vis["year"] = ISO3779_vis_get_year_from(vin)
    vin_decoded.vis["serial_number"] = ISO3779_vis_serial_number_from(vin)
    return vin_decoded

def ISO3779_dump(vin: str):
    vin_decoded = ISO3779_decode_from(vin)
    region = ISO3779_decode_region_from(vin)
    print(f"dump {{\n    wmi {{\n        region: {region}\n        country: {vin_decoded.wmi['country']}\n        manufacturer: {vin_decoded.wmi['manufacturer']}\n    }}\n    vis {{\n        year: {vin_decoded.vis['year']}\n        serial number: {vin_decoded.vis['serial_number']}\n    }}\n}}")
