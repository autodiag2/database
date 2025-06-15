#!/bin/bash
# Create a new car description (DTCs traduction, manufacturer)
#
folder="./data/vehicle"
desc="${folder}/${RANDOM}/"
descFile="${desc}/desc.ini"
codesFile="${desc}/codes.tsv"
while [ -e "${desc}" ] ; do
	desc="${folder}/${RANDOM}/"
done
mkdir -p "${desc}"
>${descFile} cat <<EOF
manufacturer=Example
ecu=Example ecu
engine=Example engine
EOF
>${codesFile}
echo "Created at ${desc} ..."
