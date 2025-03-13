
import os, sys
from decoder_modules.module import ISO3779_decoder_module
from enum import Enum

class ISO3779_decoder_toyota(ISO3779_decoder_module):
    class VehicleType(Enum):
        Passenger = 1
        Multi_purpose = 2
        Light_duty = 3
        Bus = 4
        Incomplete = 5
        Unknown = 6
    
    def __init__(self, vin: str, year: int):
        super().__init__(vin, "data/VIN/manufacturer_specific_data/toyota", year)
        self.wmi = {
            "vehicle_type": self.vehicle_type()
        }
        if 2009 <= year:
            self.vds = {
                "Body Type & Drive Wheels":         self.y2010_body_type_drive_wheels(),
                "Body Type, Drive Wheels, & Grade": self.y2010_body_type_drive_wheels_grade()
            }
    
    def y2010_body_type_drive_wheels(self):
        vt = self.vehicle_type_enum()
        if vt == ISO3779_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/body_type_drive_wheels.tsv", 1, self.vds_raw[0])
        elif vt == ISO3779_decoder_toyota.VehicleType.Multi_purpose:
            return self.lookup_tsv("2010/multi_purpose/body_type_drive_wheels.tsv", 1, self.vds_raw[0])
        elif vt == ISO3779_decoder_toyota.VehicleType.Light_duty:
            return self.lookup_tsv("2010/light_duty/body_type_drive_wheels.tsv", 1, self.vds_raw[0])
        return self.vds_raw[0]
    
    def y2010_body_type_drive_wheels_grade(self):
        vt = self.vehicle_type_enum()
        if vt == ISO3779_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/body_type_drive_wheels_grade.tsv", 1, self.vds_raw[1])
        elif vt == ISO3779_decoder_toyota.VehicleType.Multi_purpose:
            return self.lookup_tsv("2010/multi_purpose/body_type_drive_wheels_grade.tsv", 1, self.vds_raw[1])
        elif vt == ISO3779_decoder_toyota.VehicleType.Light_duty:
            print("TODO missing data here")
            return self.lookup_tsv("2010/light_duty/body_type_drive_wheels_grade.tsv", 1, self.vds_raw[1])
        return self.vds_raw[0]

    def vehicle_type(self):
        return self.lookup_tsv("vehicle_type.tsv", 1, self.vin[2])
    
    def vehicle_type_enum(self):
        vt = self.vin[2]
        if vt in ['D','K','N','X','1','2','7']:
            return ISO3779_decoder_toyota.VehicleType.Passenger
        elif vt in ['A','B','F','4']:
            return ISO3779_decoder_toyota.VehicleType.Light_duty
        elif vt in ['G']:
            return ISO3779_decoder_toyota.VehicleType.Bus
        elif vt in ['E','L','M','3']:
            return ISO3779_decoder_toyota.VehicleType.Multi_purpose
        elif vt in ['5']:
            return ISO3779_decoder_toyota.VehicleType.Incomplete
        else:
            return ISO3779_decoder_toyota.VehicleType.Unknown

    def dump_string(self, padding):
        result = f"{padding}wmi:{{\n"
        for key, value in self.wmi.items():
            result += f"{padding}   {key}:\t{value}\n"
        result += f"{padding}}}\n"
        result += f"{padding}vds:{{\n"
        for key, value in self.vds.items():
            result += f"{padding}   {key}:\t{value}\n"
        result += f"{padding}}}\n"
        return result