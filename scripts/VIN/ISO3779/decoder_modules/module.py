import os

class ISO3779_decoder_module:
    def __init__(self, vin: str, data_folder: str, year: int):
        self.vin = vin
        self.vds_raw = vin[3:9]
        self.data_folder = data_folder
        self.year = year

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
    
    def vis_manufacturing_plant(self) -> str:
        return self.vin[10]