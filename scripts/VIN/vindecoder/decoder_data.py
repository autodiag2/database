
from enum import Enum

class ISO3780_WMI_REGION(Enum):
    africa = 1
    asia = 2
    europe = 3
    north_america = 4
    oceania = 5
    south_america = 6
    unknown = 7

ISO3780_WMI_REGIONS = {
    ("A","H"): ISO3780_WMI_REGION.africa,
    ("J","R"): ISO3780_WMI_REGION.asia,
    ("S","Z"): ISO3780_WMI_REGION.europe,
    ("1","5"): ISO3780_WMI_REGION.north_america,
    ("6","7"): ISO3780_WMI_REGION.oceania,
    ("8","9"): ISO3780_WMI_REGION.south_america
}