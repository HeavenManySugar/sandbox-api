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

if [ -z "$2" ]
then
    cmake --build "$1/build" --clean-first
else
    cmake --build "$1/build" --clean-first --target "$2"
fi

# run the tests and output googletest results
# 尋找所有的ut*執行檔，然後執行

# create directories for test results if they do not exist
mkdir -p "$1/grp"
mkdir -p "$1/valgrind"

for test in $(find "$1/build" -name "ut*" ! -name "*.*")
do
    $test --gtest_output=json:"$1/grp/$(basename $test).json" > /dev/null; echo Return $?
    valgrind --error-exitcode=2 --track-origins=yes --leak-check=full --log-fd=9 9>"$1/valgrind/$(basename $test).log" $test > /dev/null
done