import os
from decoder import ISO3779_Decoder

YEAR_MAPPING = {
    'M': "1991 or 2021", 'N': "1992 or 2022", 'P': "1993 or 2023", 'R': "1994 or 2024",
    'S': "1995 or 2025", 'T': "1996 or 2026", 'V': "1997 or 2027", 'W': "1998 or 2028",
    'X': "1999 or 2029", 'Y': "2000 or 2030", '1': "2001", '2': "2002", '3': "2003",
    '4': "2004", '5': "2005", '6': "2006", '7': "2007", '8': "2008", '9': "2009",
    'A': "2010", 'B': "2011", 'C': "2012", 'D': "2013", 'E': "2014", 'F': "2015",
    'G': "2016", 'H': "2017", 'J': "2018", 'K': "2019", 'L': "2020"
}

class ISO3779_decoder_module:
    def __init__(self, rootDecoder: ISO3779_Decoder, data_folder: str):
        self.rootDecoder = rootDecoder
        self.data_folder = data_folder

    def lookup_tsv(self, filename: str, match_data: str, *columns: int):
        file_path = os.path.join(self.data_folder, filename)
        if not os.path.exists(file_path):
            return "Unknown"
        
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("#"):
                    continue
                parts = line.strip().split("\t")
                if parts[0] == match_data:
                    if 1 < len(columns):
                        return tuple(parts[col] if col < len(parts) else match_data for col in columns)
                    else:
                        return parts[columns[0]] if columns[0] < len(parts) else match_data

        
        return match_data

    def vds_decode(self):
        raise NotImplementedError("Please Implement this method")
    
    def vis_decode(self):
        return {
            "year": self.vis_get_year(), 
            "manufacturing_plant": self.vis_get_manufacturing_plant(), 
            "serial_number": self.vis_get_serial_number()
        }
    
    def vis_get_year(self) -> str:
        return YEAR_MAPPING.get(self.rootDecoder.vis_raw[0], "Unknown year")
    
    def vis_get_manufacturing_plant(self) -> str:
        return self.rootDecoder.vis_raw[1]

    def vis_get_serial_number(self) -> str:
        return self.rootDecoder.vis_raw[5:] if self.rootDecoder.wmi_manufacturer_is_less_500() else self.rootDecoder.vis_raw[2:]
