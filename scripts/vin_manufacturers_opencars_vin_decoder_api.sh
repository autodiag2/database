#!/bin/bash

# URL of the manufacturers CSV file
URL="https://raw.githubusercontent.com/opencars/vin-decoder-api/refs/heads/master/manufacturers.csv"
LOCAL_FILE="data/VIN/manufacturers.tsv"
TEMP_FILE="data/VIN/manufacturers_temp.tsv"

# Download the CSV file
curl -s "$URL" | awk -F';' '1 { gsub(/"/, "", $1); gsub(/"/, "", $2); print $1 "\t" $2 }' > "$TEMP_FILE"

# Check if the file was downloaded successfully
if [ -s "$TEMP_FILE" ]; then
    tail -n +2 "$TEMP_FILE" >> "$LOCAL_FILE"
    sort -k1,1 -k3,3 -u "$LOCAL_FILE" -o "$LOCAL_FILE"
    echo "Updated $LOCAL_FILE with new entries."
else
    echo "Failed to download or process the CSV file."
fi
rm -f "$TEMP_FILE"