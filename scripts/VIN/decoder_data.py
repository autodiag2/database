
from enum import Enum

ISO3780_WMI_COUNTRIES = {
    ("AA", "AH"): "south africa", ("AJ", "AN"): "ivory coast",
    ("BA", "BE"): "angola", ("BF", "BK"): "kenya", ("BL", "BR"): "tanzania",
    ("CA", "CE"): "benin", ("CF", "CK"): "madagascar",
    ("CL", "CR"): "tunisia", ("DA", "DE"): "egypt",
    ("DF", "DK"): "morocco", ("DL", "DR"): "zambia",
    ("EA", "EE"): "ethiopia", ("EF", "EK"): "mozambique",
    ("FA", "FE"): "ghana", ("FF", "FK"): "nigeria",
    ("JA", "J0"): "japan", ("KA", "KE"): "sri lanka",
    ("KF", "KK"): "israel", ("KL", "KR"): "south korea",
    ("LA", "L0"): "china", ("MA", "ME"): "india",
    ("MF", "MK"): "indonesia", ("ML", "MR"): "thailand",
    ("NF", "NK"): "pakistan", ("NL", "NR"): "turkey",
    ("PA", "PE"): "philippines", ("PF", "PK"): "singapore",
    ("PL", "PR"): "malaysia", ("RA", "RE"): "united arab emirates",
    ("RF", "RK"): "taiwan", ("RL", "RR"): "vietnam",
    ("SA", "SM"): "great britain", ("VF", "VR"): "france",
    ("WA", "W0"): "germany", ("ZA", "ZR"): "italy",
}

class ISO3780_WMI_REGION(Enum):
    africa = 1
    asia = 2
    europe = 3
    north_ameria = 4
    oceania = 5
    south_america = 6
    unknown = 7

ISO3780_WMI_REGIONS = {
    ("A","H"): ISO3780_WMI_REGION.africa,
    ("J","R"): ISO3780_WMI_REGION.asia,
    ("S","Z"): ISO3780_WMI_REGION.europe,
    ("1","5"): ISO3780_WMI_REGION.north_ameria,
    ("6","7"): ISO3780_WMI_REGION.oceania,
    ("8","9"): ISO3780_WMI_REGION.south_america
}