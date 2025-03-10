#!/bin/bash

LOCAL_FILE="data/VIN/manufacturers.tsv"

# Extraire et afficher les paires WMI\tManufacturer
curl -s https://raw.githubusercontent.com/sunrise-php/vin/refs/heads/master/data/manufacturers.php | 
 grep -o -E "'([A-Z0-9]{2,3})'.*" | while read -r line; do
    tabline=$(echo "$line" | sed "s/'\([A-Z0-9]\{2,3\}\)' *=> *'\(.*\)',*/\1\t\2/")
    echo "$tabline" >> "$LOCAL_FILE"
done

sort -k1,1 -u "$LOCAL_FILE" -o "$LOCAL_FILE"
echo "Updated $LOCAL_FILE with new entries."