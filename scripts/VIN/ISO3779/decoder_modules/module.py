import os
from decoder import ISO3779_Decoder


YEAR_MAPPING = ['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F','G','H','J','K','L','M','N','P','R','S','T','V','W','X','Y']

class VIN_decoder_module:
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
    
    def vis_get_year(self) -> int:
        period_offset = YEAR_MAPPING.index(self.rootDecoder.vis_raw[0])
        if period_offset == -1:
            return None
        offset_to_start = (self.rootDecoder.year - 1971) % len(YEAR_MAPPING)
        period_year = self.rootDecoder.year - offset_to_start + period_offset
        return period_year
    
    def vis_get_manufacturing_plant(self) -> str:
        return self.rootDecoder.vis_raw[1]

    def vis_get_serial_number(self) -> str:
        return self.rootDecoder.vis_raw[5:] if self.rootDecoder.wmi_manufacturer_is_less_500() else self.rootDecoder.vis_raw[2:]
