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
engine=Example engine
model=Example model
EOF
>${codesFile}
echo "Created at ${desc} ..."
