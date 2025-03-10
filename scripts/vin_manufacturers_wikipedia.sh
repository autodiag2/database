#!/bin/bash

# https://en.wikipedia.org/wiki/Vehicle_identification_number
LOCAL_FILE="data/VIN/manufacturers.tsv"
cat "scripts/wikipedia_sae_wmi_manufacturers.tsv" >> .temp
cat "$LOCAL_FILE" >> .temp
sort -k1,1 -u .temp -o "$LOCAL_FILE"
rm .temp
echo "Updated $LOCAL_FILE with new entries."
