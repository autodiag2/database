#!/bin/bash
# Create a new car description (DTCs traduction, brand)
#
folder="./data/car"
desc="${folder}/${RANDOM}/"
descFile="${desc}/desc.ini"
codesFile="${desc}/codes.tsv"
while [ -e "${desc}" ] ; do
	desc="${folder}/${RANDOM}/"
done
mkdir -p "${desc}"
>${descFile} cat <<EOF
brand=Example
ecu=Example ecu
model=Example model
EOF
>${codesFile}
echo "Created at ${desc} ..."
