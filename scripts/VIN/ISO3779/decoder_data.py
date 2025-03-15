
from enum import Enum

ISO3780_WMI_COUNTRIES = {
    ("AA", "AH"): "South Africa", ("AJ", "AN"): "Ivory Coast", ("AP", "A0"): "Unassigned",
    ("BA", "BE"): "Angola", ("BF", "BK"): "Kenya", ("BL", "BR"): "Tanzania",
    ("BS", "B0"): "Unassigned", ("CA", "CE"): "Benin", ("CF", "CK"): "Madagascar",
    ("CL", "CR"): "Tunisia", ("CS", "C0"): "Unassigned", ("DA", "DE"): "Egypt",
    ("DF", "DK"): "Morocco", ("DL", "DR"): "Zambia", ("DS", "D0"): "Unassigned",
    ("EA", "EE"): "Ethiopia", ("EF", "EK"): "Mozambique", ("EL", "E0"): "Unassigned",
    ("FA", "FE"): "Ghana", ("FF", "FK"): "Nigeria", ("FL", "F0"): "Unassigned",
    ("GA", "G0"): "Unassigned", ("HA", "H0"): "Unassigned", ("JA", "J0"): "Japan",
    ("KA", "KE"): "Sri Lanka", ("KF", "KK"): "Israel", ("KL", "KR"): "South Korea",
    ("KS", "K0"): "Unassigned", ("LA", "L0"): "China", ("MA", "ME"): "India",
    ("MF", "MK"): "Indonesia", ("ML", "MR"): "Thailand", ("MS", "M0"): "Unassigned",
    ("NF", "NK"): "Pakistan", ("NL", "NR"): "Turkey", ("NS", "N0"): "Unassigned",
    ("PA", "PE"): "Philippines", ("PF", "PK"): "Singapore", ("PL", "PR"): "Malaysia",
    ("PS", "P0"): "Unassigned", ("RA", "RE"): "United Arab Emirates", ("RF", "RK"): "Taiwan",
    ("RL", "RR"): "Vietnam", ("RS", "R0"): "Unassigned", ("SA", "SM"): "Great Britain",
    ("VF", "VR"): "France", ("WA", "W0"): "Germany", ("ZA", "ZR"): "Italy",
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