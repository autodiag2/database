#!/bin/bash

LOCAL_FILE="data/VIN/manufacturers.tsv"
cat "scripts/wikipedia_sae_wmi_manufacturers.tsv" >> "$LOCAL_FILE"
sort -k1,1 -u "$LOCAL_FILE" -o "$LOCAL_FILE"
echo "Updated $LOCAL_FILE with new entries."
