import re

SAEJ2012_2002_RE = re.compile(r"^[PCBU][0-3][0-9A-F]{3}$", re.IGNORECASE)

def is_saej2012_2002(code: str) -> bool:
    return SAEJ2012_2002_RE.match(code.strip()) is not None

def is_manufacturer_specific_saej2012_2002(code: str) -> bool:
    code = code.strip().upper()

    if not is_saej2012_2002(code):
        return False

    if code[0] == 'B' or code[0] == 'C' or code[0] == 'U':
        if code[1] == "2":
            return True
    return code[1] == "1"