
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
    
    def __init__(self, year: int,  region: str, vin: str):
        super().__init__(vin, "data/VIN/manufacturer_specific_data/toyota", year)

    def vds_decode(self):
        is_na1996 = False
        print("TODO more proper way to handle this")
        if True or region == "North America":
            if 2010 <= self.year:
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
        else:
            if 2002 <= self.year:
                is_na1996 = True
        
        if is_na1996:
            print("TODO 1996-2009 format")

    def na2010_body_type_drive_wheels(self):
        vt = self.vehicle_type_enum()
        if vt == ISO3779_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv(f"2010/passenger/body_type_drive_wheels.tsv", self.vds_raw[0], 1)
        elif vt == ISO3779_decoder_toyota.VehicleType.Multi_purpose:
            return self.lookup_tsv(f"2010/multi_purpose/body_type_drive_wheels.tsv", self.vds_raw[0], 1)
        elif vt == ISO3779_decoder_toyota.VehicleType.Light_duty:
            return self.lookup_tsv(f"2010/light_duty/body_type_drive_wheels.tsv", self.vds_raw[0], 1)
        return self.vds_raw[0]
    
    def na2010_body_type_drive_wheels_grade(self):
        vt = self.vehicle_type_enum()
        if vt == ISO3779_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/body_type_drive_wheels_grade.tsv", self.vds_raw[0], 1)
        elif vt == ISO3779_decoder_toyota.VehicleType.Multi_purpose:
            return self.lookup_tsv("2010/multi_purpose/body_type_drive_wheels_grade.tsv", self.vds_raw[0], 1)
        elif vt == ISO3779_decoder_toyota.VehicleType.Light_duty:
            print("TODO missing data here")
            return self.lookup_tsv("2010/light_duty/body_type_drive_wheels_grade.tsv", self.vds_raw[0], 1)
        return self.vds_raw[0]
    
    def na2010_engine_type(self):
        print("TODO : electric & fuel cell")
        return self.lookup_tsv("2010/engine_type.tsv", self.vds_raw[1], 1, 2, 3, 4, 5)
    
    def na2010_restraint_system(self):
        return self.lookup_tsv("2010/restraint_system.tsv", self.vds_raw[2], 1, 2)
    
    def na2010_series(self):
        vt = self.vehicle_type_enum()
        if vt == ISO3779_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/series.tsv", self.vds_raw[3], 1)
        elif vt == ISO3779_decoder_toyota.VehicleType.Multi_purpose or vt == ISO3779_decoder_toyota.VehicleType.Light_duty:
            return self.lookup_tsv("2010/multi_purpose/series.tsv", self.vds_raw[3], 1)
        return self.vds_raw[3]
    
    def na2010_series_drive_wheels(self):
        vt = self.vehicle_type_enum()
        if vt == ISO3779_decoder_toyota.VehicleType.Passenger:
            return self.lookup_tsv("2010/passenger/series_drive_wheels.tsv", self.vds_raw[3], 1)
        elif vt == ISO3779_decoder_toyota.VehicleType.Multi_purpose or vt == ISO3779_decoder_toyota.VehicleType.Light_duty:
            return self.lookup_tsv("2010/multi_purpose/series_drive_wheels.tsv", self.vds_raw[3], 1)
        return self.vds_raw[3]
    
    def na2010_vehicle_line_make(self):
        return self.lookup_tsv("2010/vehicle_line_make.tsv", self.vds_raw[4], 1)
    
    def vehicle_type(self):
        return self.lookup_tsv("vehicle_type.tsv", self.vin[2], 1)

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
