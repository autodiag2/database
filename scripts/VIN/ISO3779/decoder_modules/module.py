import os

class ISO3779_decoder_module:
    def __init__(self, vin: str, data_folder: str):
        self.vin = vin
        self.vds_raw = vin[3:9]
        self.data_folder = data_folder

    def _lookup_tsv(self, filename: str, column: int, match_data: str) -> str:
            file_path = os.path.join(self.data_folder, filename)
            print(file_path)
            if not os.path.exists(file_path):
                return "Unknown"
            
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    if line.startswith("#"):
                        continue
                    parts = line.strip().split("\t")
                    if parts[0] == match_data:
                        return parts[column] if len(parts) > column else match_data
            return match_data
    
    def dump(self):
        print(self.dump_string(""))