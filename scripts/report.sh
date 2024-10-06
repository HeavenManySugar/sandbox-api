#!/bin/bash

# check if the first argument is a directory
if [ ! -d "$1" ]
then
    echo "The path provided is not a directory"
    exit 1
fi

# check if the directory is empty
if [ -z "$(ls -A "$1")" ]
then
    echo "The directory is empty"
    exit 1
fi

# check if the second argument is provided and is a file
if [ -n "$1/$2.json" ] && [ -f "$1/$2.json" ]
then
    python3 ./utils/grp_parser.py "$1/$2.json"
else
    for report in $(find "$1" -name "*.json")
    do
        python3 ./utils/grp_parser.py "$report"
    done
fi
