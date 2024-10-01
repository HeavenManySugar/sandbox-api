#!/bin/bash

# check if the argument is a directory
if [ ! -d "$1" ]
then
    echo "The path provided is not a directory"
    exit 1
fi

# check if the directory is empty
if [ -z "$(ls -A $1)" ]
then
    echo "The directory is empty"
    exit 1
fi

# check if the directory contains a CMakeLists.txt file
if [ ! -f "$1/CMakeLists.txt" ]
then
    echo "The directory does not contain a CMakeLists.txt file"
    exit 1
fi

# clean cmake cache
# rm -rf "$1/build"

# build the project
cmake -S "$1" -B "$1/build" -G Ninja -DCMAKE_BUILD_TYPE=Debug -DFETCH_GOOGLETEST=OFF
cmake --build "$1/build"

# run the tests and output googletest results
# 尋找所有的ut*執行檔，然後執行
for test in $(find "$1/build" -name "ut*" ! -name "*.*")
do
    $test --gtest_output=json:"./tmp/isolate-runner/$(basename $test).json" > /dev/null; echo Return $?
    valgrind --error-exitcode=2 --track-origins=yes --leak-check=full --log-fd=9 9>./tmp/isolate-runner/$(basename $test).log $test > /dev/null
    python3 ./grp-parser.py ./tmp/isolate-runner/$(basename $test).json
done