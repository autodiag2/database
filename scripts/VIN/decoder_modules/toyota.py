
# https://en.wikibooks.org/wiki/Vehicle_Identification_Numbers_(VIN_codes)/Toyota/VIN_Codes
import os, sys
from decoder_modules.module import VIN_decoder_module
from enum import Enum
from decoder import *

class VIN_decoder_toyota(VIN_decoder_module):
    class VehicleType(Enum):
        Passenger = 1
        Multi_purpose = 2
        Light_duty = 3
        Bus = 4
        Incomplete = 5
        Unknown = 6
    
    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "data/VIN/manufacturer_specific_data/toyota")

    def vds_decode(self):
        is_na1996 = False
        if 2010 <= self.rootDecoder.year:
            return {
                "Body Type & Drive Wheels":         self.na2010_body_type_drive_wheels(),
                "Body Type, Drive Wheels, & Grade": self.na2010_body_type_drive_wheels_grade(),
                "Engine Type":                      self.na2010_engine_type(),
                "Restraint System":                 self.na2010_restraint_system(),
                "Series":                           self.na2010_series(),
                "Series & Drive Wheels":            self.na2010_series_drive_wheels(),
                "Vehicle Line & Make":              self.na2010_vehicle_line_make()
            }
        else:
            is_na1996 = True
        
        if is_na1996:
            print("TODO 1996-2009 format")

    def na2010_body_type_drive_wheels(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv(f"2010/passenger/body_type_drive_wheels.tsv", self.rootDecoder.vds_raw[0], 1)
        elif vt == VIN_decoder_toyota.VehicleType.Multi_purpose:
            return self.lookup_tsv(f"2010/multi_purpose/body_type_drive_wheels.tsv", self.rootDecoder.vds_raw[0], 1)
        elif vt == VIN_decoder_toyota.VehicleType.Light_duty:
            return self.lookup_tsv(f"2010/light_duty/body_type_drive_wheels.tsv", self.rootDecoder.vds_raw[0], 1)
        return self.rootDecoder.vds_raw[0]
    
    def na2010_body_type_drive_wheels_grade(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/body_type_drive_wheels_grade.tsv", self.rootDecoder.vds_raw[0], 1)
        elif vt == VIN_decoder_toyota.VehicleType.Multi_purpose:
            return self.lookup_tsv("2010/multi_purpose/body_type_drive_wheels_grade.tsv", self.rootDecoder.vds_raw[0], 1)
        elif vt == VIN_decoder_toyota.VehicleType.Light_duty:
            print("TODO missing data here")
            return self.lookup_tsv("2010/light_duty/body_type_drive_wheels_grade.tsv", self.rootDecoder.vds_raw[0], 1)
        return self.rootDecoder.vds_raw[0]
    
    def na2010_engine_type(self):
        print("TODO : electric & fuel cell")
        return self.lookup_tsv("2010/engine_type.tsv", self.rootDecoder.vds_raw[1], 1, 2, 3, 4, 5)
    
    def na2010_restraint_system(self):
        return self.lookup_tsv("2010/restraint_system.tsv", self.rootDecoder.vds_raw[2], 1, 2)
    
    def na2010_series(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/series.tsv", self.rootDecoder.vds_raw[3], 1)
        elif vt == VIN_decoder_toyota.VehicleType.Multi_purpose or vt == VIN_decoder_toyota.VehicleType.Light_duty:
            return self.lookup_tsv("2010/multi_purpose/series.tsv", self.rootDecoder.vds_raw[3], 1)
        return self.rootDecoder.vds_raw[3]
    
    def na2010_series_drive_wheels(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/series_drive_wheels.tsv", self.rootDecoder.vds_raw[3], 1)
        elif vt == VIN_decoder_toyota.VehicleType.Multi_purpose or vt == VIN_decoder_toyota.VehicleType.Light_duty:
            return self.lookup_tsv("2010/multi_purpose/series_drive_wheels.tsv", self.rootDecoder.vds_raw[3], 1)
        return self.rootDecoder.vds_raw[3]
    
    def na2010_vehicle_line_make(self):
        return self.lookup_tsv("2010/vehicle_line_make.tsv", self.rootDecoder.vds_raw[4], 1)
    
    def vis_get_manufacturing_plant(self) -> str:
        return self.lookup_tsv("plant.tsv", self.rootDecoder.vis_raw[1], 1)
    
    def vehicle_type(self):
        return self.lookup_tsv("vehicle_type.tsv", self.vin[2], 1)

    def vehicle_type_enum(self):
        vt = self.rootDecoder.wmi_raw[2]
        if vt in ['D','K','N','X','1','2','7']:
            return VIN_decoder_toyota.VehicleType.Passenger
        elif vt in ['A','B','F','4']:
            return VIN_decoder_toyota.VehicleType.Light_duty
        elif vt in ['G']:
            return VIN_decoder_toyota.VehicleType.Bus
        elif vt in ['E','L','M','3']:
            return VIN_decoder_toyota.VehicleType.Multi_purpose
        elif vt in ['5']:
            return VIN_decoder_toyota.VehicleType.Incomplete
        else:
            return VIN_decoder_toyota.VehicleType.Unknown
