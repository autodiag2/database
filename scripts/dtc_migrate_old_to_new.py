# migrate the old database to new system, yml definition for codes
import csv
import configparser
import yaml
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import sys

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

# Input / output directories
INPUT_DIR = Path('data/vehicle')
OUTPUT_DIR = Path('output/vehicle')

# Current timestamp
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Function to check if code is generic
def is_generic_code(code: str) -> bool:
    if len(code) < 5:
        return False
    first_char = code[0].upper()
    second_char = code[1]
    return second_char == '0' and first_char in ('P','C','B','U')

# SAEJ2012 definition
def is_manufacturer_specific(code: str) -> bool:
    if len(code) < 5:
        return False
    first_char = code[0].upper()
    second_char = code[1]
    if first_char == 'P' and ( second_char == '1' or second_char == '3' ):
        return True
    if first_char == 'B' and ( second_char == '1' or second_char == '2' ):
        return True
    if first_char == 'C' and ( second_char == '1' or second_char == '2' ):
        return True
    if first_char == 'U' and ( second_char == '1' or second_char == '2' ):
        return True

# Threshold for long lines to warn
LONG_LINE_THRESHOLD = 200

# Find all desc.ini files
desc_files = list(INPUT_DIR.rglob('desc.ini'))

for desc_file in tqdm(desc_files, desc="Processing desc.ini files"):
    folder = desc_file.parent
    codes_file = folder / 'codes.tsv'
    if not codes_file.exists():
        continue

    is_generic_folder = folder.name.lower() == 'generic'

    # Read desc.ini safely
    config = configparser.ConfigParser()
    try:
        config.read(desc_file)
    except configparser.MissingSectionHeaderError:
        with open(desc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = '[DEFAULT]\n' + content
        config.read_string(content)

    manufacturer = config.get('DEFAULT', 'manufacturer', fallback='')
    engine = config.get('DEFAULT', 'engine', fallback='')
    ecu = config.get('DEFAULT', 'ecu', fallback='')

    # Process each DTC
    with open(codes_file, newline='\n', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        for row in reader:
            if not row or len(row) < 2:
                continue
            code, definition = row[0], row[1]

            # Warn on long lines
            if len(definition) > LONG_LINE_THRESHOLD:
                print(f"WARNING: DTC {code} has a long definition ({len(definition)} chars):")
                print(definition[:200] + '...')

            # Skip generic codes unless in 'generic' folder
            if (not is_manufacturer_specific(code) or definition.startswith("ISO/SAE Reserved")) and not is_generic_folder:
                continue

            
            entry = {
                'scope': {
                    'vehicle': [
                        {
                            'manufacturer': manufacturer if is_manufacturer_specific(code) else 'saej2012.2002',
                            'model': '',
                            'engine': engine,
                            'ecu': ecu,
                            'years': 'any'
                        }
                    ],
                    'protocol': ['obd2'],
                    'standard': ["saej2012.2002"]
                },
                'code': code,
                'system': '',
                'subsystem': '',
                'category': '',
                'definition': definition,
                'description': '',
                'severity': '',
                'mil': '',
                'created': now,
                'updated': now,
                'related_code': [],
                'detection_condition': [],
                'causes': [],
                'repairs': [],
                'evidence': {
                    'source': ['obdcodex']
                }
            }

            # Build output path inside "dtc" folder
            relative_path = folder.relative_to(INPUT_DIR)
            out_dir = OUTPUT_DIR / relative_path / 'dtc'
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f'{code}.yml'

            # Write YAML file
            with open(out_file, 'w', encoding='utf-8') as f:
                yaml.dump(entry, f, sort_keys=False, allow_unicode=True)
