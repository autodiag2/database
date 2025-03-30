from vindecoder.decoder_modules.module import VIN_decoder_module
from vindecoder.decoder import ISO3779_Decoder
from enum import Enum

class VIN_decoder_alpha_romeo(VIN_decoder_module):

    class VehicleType(Enum):
        Passenger = 1
        Multi_purpose = 2
        Unknown = 3

    def __init__(self, rootDecoder: ISO3779_Decoder):
        super().__init__(rootDecoder, "data/manufacturer_specific/alpha_romeo")
    
    def vis_get_manufacturing_plant(self) -> str:
        return self.lookup_tsv("plant.tsv", self.rootDecoder.vis_raw[1], 1)
    
    def vehicle_type_enum(self):
        vt = self.rootDecoder.wmi_raw[2]
        if vt in ['R']:
            return VIN_decoder_alpha_romeo.VehicleType.Passenger
        elif vt in ['S']:
            return VIN_decoder_alpha_romeo.VehicleType.Multi_purpose
        else:
            return VIN_decoder_alpha_romeo.VehicleType.Unknown
    
    def vds_restraint_system(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_alpha_romeo.VehicleType.Passenger:
            return self.lookup_tsv("passenger/restraint_system.tsv", self.rootDecoder.vds_raw[0], 1)
        elif vt == VIN_decoder_alpha_romeo.VehicleType.Multi_purpose:
            return self.lookup_tsv("multi_purpose/restraint_system.tsv", self.rootDecoder.vds_raw[0], 1)
        return self.rootDecoder.vds_raw[0]
    
    def vds_get_brand(self):
        return self.lookup_tsv("brand.tsv", self.rootDecoder.vis_raw[1], 1)
    
    def vds_marketing_name_drive_wheels(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_alpha_romeo.VehicleType.Passenger:
            return self.lookup_tsv("passenger/marketing_name_&_drive_wheels.tsv", self.rootDecoder.vds_raw[2], 1)
        elif vt == VIN_decoder_alpha_romeo.VehicleType.Multi_purpose:
            return self.lookup_tsv("multi_purpose/marketing_name_&_drive_wheels.tsv", self.rootDecoder.vds_raw[2], 1)
        return self.rootDecoder.vds_raw[2]

    def vds_price_series_drive_wheels_drive_position_body_style(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_alpha_romeo.VehicleType.Passenger:
            return self.lookup_tsv("passenger/price_series_drive_wheels_drive_position_body_style.tsv", self.rootDecoder.vds_raw[3], 1)
        elif vt == VIN_decoder_alpha_romeo.VehicleType.Multi_purpose:
            return self.lookup_tsv("multi_purpose/price_series_drive_wheels_drive_position_body_style.tsv", self.rootDecoder.vds_raw[3], 1)
        return self.rootDecoder.vds_raw[3]
    
    def vds_engine(self):
        vt = self.vehicle_type_enum()
        if vt == VIN_decoder_alpha_romeo.VehicleType.Passenger:
            return self.lookup_tsv("passenger/engine.tsv", self.rootDecoder.vds_raw[4], 1, 2, 3, 4, 5)
        elif vt == VIN_decoder_alpha_romeo.VehicleType.Multi_purpose:
            return self.lookup_tsv("multi_purpose/engine.tsv", self.rootDecoder.vds_raw[4], 1, 2, 3, 4, 5)
        return self.rootDecoder.vds_raw[4]

    def vds_decode(self):
        return {
            'restraint_system': self.vds_restraint_system(),
            'brand': self.vds_get_brand(),
            'vds_marketing_name_drive_wheels': self.vds_marketing_name_drive_wheels(),
            'price_series_drive_wheels_drive_position_body_style': self.vds_price_series_drive_wheels_drive_position_body_style(),
            'engine': self.vds_engine()
        }