from vindecoder.decoder_modules.module import VIN_decoder_module
from vindecoder.decoder import ISO3779_Decoder
from enum import Enum

class VIN_decoder_chrysler(VIN_decoder_module):

    class VehicleType(Enum):
        Passenger = 1
        Multi_purpose = 2
        Unknown = 3

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "data/manufacturer_specific/chrysler")
    
    def vds_decode(self):
        return {
            "restraint_system": self.vds_restraint_system(),
            "brand": self.vds_brand(),
            "marketing_name": self.vds_marketing_name(),
            "price_series": self.vds_price_series(),
            "engine": self.vds_engine(),
        }
             
    def vehicle_type_enum(self):
        vt = self.rootDecoder.wmi_raw[2]
        if vt in ['3']:
            return VIN_decoder_chrysler.VehicleType.Passenger
        elif vt in ['4', '6']:
            return VIN_decoder_chrysler.VehicleType.Multi_purpose
        else:
            return VIN_decoder_chrysler.VehicleType.Unknown
        
    def vds_restraint_system(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_chrysler.VehicleType.Passenger:
            return self.lookup_tsv("passenger/restraint_system.tsv", self.rootDecoder.vds_raw[0], 1)
        elif vt == VIN_decoder_chrysler.VehicleType.Multi_purpose:
            return self.lookup_tsv("light_truck_multi/gvwr_brake_restraint_system.tsv", self.rootDecoder.vds_raw[0], 1)
        return self.rootDecoder.vds_raw[0]

    def vds_brand(self):
        return self.lookup_tsv("brand.tsv", self.rootDecoder.vds_raw[1], 1)
    
    def vds_marketing_name(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_chrysler.VehicleType.Passenger:
            return self.lookup_tsv("passenger/marketing_name.tsv", self.rootDecoder.vds_raw[2], 1)
        elif vt == VIN_decoder_chrysler.VehicleType.Multi_purpose:
            return self.lookup_tsv("light_truck_multi/marketing_name_drive_wheels.tsv", self.rootDecoder.vds_raw[2], 1)
        return self.rootDecoder.vds_raw[2]
    
    def vds_price_series(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_chrysler.VehicleType.Passenger:
            return self.lookup_tsv("passenger/price_series.tsv", self.rootDecoder.vds_raw[3], 1)
        return self.rootDecoder.vds_raw[3]
    
    def vds_engine(self):
        print("TODO electric cars")
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_chrysler.VehicleType.Passenger:
            return self.lookup_tsv("passenger/engine.tsv", self.rootDecoder.vds_raw[4], 1, 2, 3, 4, 5)
        elif vt == VIN_decoder_chrysler.VehicleType.Multi_purpose:
            return self.lookup_tsv("light_truck_multi/engine.tsv", self.rootDecoder.vds_raw[4], 1, 2, 3, 4, 5)
        return self.rootDecoder.vds_raw[4]
        
    def vis_get_manufacturing_plant(self) -> str:
        return self.lookup_tsv("plant.tsv", self.rootDecoder.vis_raw[1], 1)
    